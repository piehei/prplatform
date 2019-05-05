from django.test import RequestFactory, TestCase
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

import datetime

from prplatform.users.models import User, StudentGroup
from prplatform.courses.models import Course
from prplatform.exercises.models import SubmissionExercise, ReviewExercise
from prplatform.exercises.question_models import Question

from prplatform.submissions.models import (
    Answer,
    OriginalSubmission,
    ReviewSubmission,
    DownloadToken,
)

from prplatform.submissions.reviewlock_models import ReviewLock
from prplatform.submissions.views import (
    DownloadSubmissionView,
    OriginalSubmissionDeleteView,
    OriginalSubmissionListView,
    ReviewSubmissionListView,
    ReviewSubmissionDetailView,
    ReviewSubmissionDeleteView,
)


class SubmissionsTest(TestCase):
    fixtures = ["courses.yaml"]

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.kwargs = {'base_url_slug': 'prog1', 'url_slug': 'F2018'}

        self.s1 = User.objects.get(username="student1")
        self.s2 = User.objects.get(username="student2")
        self.s3 = User.objects.get(username="student3")
        self.s4 = User.objects.get(username="student4")

        self.students = [self.s1, self.s2, self.s3, self.s4]

        self.t1 = User.objects.get(username="teacher1")
        self.course = Course.objects.get(pk=1)

    def test_studentCanOnlyViewPersonalSubmissions(self):

        exercise = SubmissionExercise.objects.get(pk=1)

        for username in ["student1", "student2", "student3"]:
            user = User.objects.get(username=username)
            OriginalSubmission(course=self.course, submitter_user=user, exercise=exercise, text="jadajada").save()

        request = self.factory.get('/courses/prog1/F2018/submissions/s/1/list/')
        request.user = User.objects.get(username="student1")
        self.kwargs['pk'] = 1

        response = OriginalSubmissionListView.as_view()(request, **self.kwargs)

        self.assertEqual(OriginalSubmission.objects.all().count(), 3)
        self.assertEqual(response.context_data['object_list'].count(), 1)
        self.assertNotContains(response, "student2")  # hacky
        self.assertNotContains(response, "student3")

        ######################
        #
        # same thing for group submissions
        #

        OriginalSubmission.objects.all().delete()

        g1 = StudentGroup.objects.create(course=self.course, name='group1', student_usernames=[
                                         'student1@prp.fi', 'student2@prp.fi'])
        g2 = StudentGroup.objects.create(course=self.course, name='group2', student_usernames=['student3@prp.fi'])

        exercise.use_groups = True
        exercise.save()

        OriginalSubmission(course=self.course, exercise=exercise, text='jada jada',
                           submitter_user=User.objects.get(username='student1'),
                           submitter_group=g1).save()
        # both group members should see 1
        request = self.factory.get('/courses/prog1/F2018/submissions/s/1/list/')
        request.user = User.objects.get(username="student1")
        response = OriginalSubmissionListView.as_view()(request, **self.kwargs)
        self.assertEqual(response.context_data['object_list'].count(), 1)
        self.assertEqual(response.context_data['object_list'].first().submitter_group, g1)
        self.assertContains(response, 'group1')

        request = self.factory.get('/courses/prog1/F2018/submissions/s/1/list/')
        request.user = User.objects.get(username="student2")
        response = OriginalSubmissionListView.as_view()(request, **self.kwargs)
        self.assertEqual(response.context_data['object_list'].count(), 1)
        self.assertEqual(response.context_data['object_list'].first().submitter_group, g1)
        self.assertContains(response, 'group1')

        # outsider should see nothing
        request = self.factory.get('/courses/prog1/F2018/submissions/s/1/list/')
        request.user = User.objects.get(username="student3")
        response = OriginalSubmissionListView.as_view()(request, **self.kwargs)
        self.assertEqual(response.context_data['object_list'].count(), 0)
        self.assertNotContains(response, 'group1')

        OriginalSubmission(course=self.course, exercise=exercise, text='jada jada',
                           submitter_user=User.objects.get(username='student2'),
                           submitter_group=g1).save()

        OriginalSubmission(course=self.course, exercise=exercise, text='jada jada',
                           submitter_user=User.objects.get(username='student3'),
                           submitter_group=g2).save()

        # g1 nenbers should see two submissions
        request = self.factory.get('/courses/prog1/F2018/submissions/s/1/list/')
        request.user = User.objects.get(username="student1")
        response = OriginalSubmissionListView.as_view()(request, **self.kwargs)
        self.assertEqual(response.context_data['object_list'].count(), 2)
        self.assertEqual(response.context_data['object_list'].first().submitter_group, g1)
        self.assertNotContains(response, 'group2')
        self.assertContains(response, 'group1')

        request = self.factory.get('/courses/prog1/F2018/submissions/s/1/list/')
        request.user = User.objects.get(username="student2")
        response = OriginalSubmissionListView.as_view()(request, **self.kwargs)
        self.assertEqual(response.context_data['object_list'].count(), 2)
        self.assertEqual(response.context_data['object_list'].first().submitter_group, g1)
        self.assertNotContains(response, 'group2')
        self.assertContains(response, 'group1')

        # g2 member should see one submission
        request = self.factory.get('/courses/prog1/F2018/submissions/s/1/list/')
        request.user = User.objects.get(username="student3")
        response = OriginalSubmissionListView.as_view()(request, **self.kwargs)
        self.assertEqual(response.context_data['object_list'].count(), 1)
        self.assertEqual(response.context_data['object_list'].first().submitter_group, g2)
        self.assertNotContains(response, 'group1')
        self.assertContains(response, 'group2')

        # submissions not belonging to any group
        # this could happen if the teacher changed use_groups later on
        OriginalSubmission(course=self.course, exercise=exercise, text='jada jada',
                           submitter_user=User.objects.get(username='student2'),
                           ).save()
        OriginalSubmission(course=self.course, exercise=exercise, text='jada jada',
                           submitter_user=User.objects.get(username='student3'),
                           ).save()
        # student4 should see nothing since he's not in a group and has submitted
        # nothing
        request = self.factory.get('/courses/prog1/F2018/submissions/s/1/list/')
        request.user = User.objects.get(username="student4")
        response = OriginalSubmissionListView.as_view()(request, **self.kwargs)
        self.assertEqual(response.context_data['object_list'].count(), 0)
        self.assertNotContains(response, 'group1')
        self.assertNotContains(response, 'group2')

    def test_teacherCanViewAllSubmissions(self):

        exercise = SubmissionExercise.objects.get(pk=1)

        for username in ["student1", "student2", "student3", "teacher1"]:
            user = User.objects.get(username=username)
            OriginalSubmission(course=self.course, submitter_user=user, exercise=exercise, text="jadajada").save()

        request = self.factory.get('/courses/prog1/F2018/submissions/s/1/list/')
        request.user = User.objects.get(username="teacher1")
        self.kwargs['pk'] = 1

        response = OriginalSubmissionListView.as_view()(request, **self.kwargs)

        self.assertEqual(OriginalSubmission.objects.all().count(), 4)
        self.assertEqual(response.context_data['object_list'].count(), 4)
        self.assertContains(response, "student1")  # hacky
        self.assertContains(response, "student2")
        self.assertContains(response, "student3")
        self.assertContains(response, "teacher1")

    def test_ReviewSubmissionListPermissionsWork(self):

        sub_exercise = SubmissionExercise.objects.get(pk=1)
        rev_exercise = ReviewExercise.objects.get(pk=1)

        for user in self.students[:2]:
            OriginalSubmission(course=self.course, submitter_user=user, exercise=sub_exercise, text="jadajada").save()

        for user in self.students[:2]:
            revsub = OriginalSubmission.objects.filter(exercise=sub_exercise) \
                .exclude(submitter_user=user).first()
            ReviewSubmission(course=self.course, submitter_user=user,
                             exercise=rev_exercise, reviewed_submission=revsub).save()

        # teacher sees all reviews
        request = self.factory.get('/courses/prog1/F2018/submissions/r/1/list/')
        request.user = User.objects.get(username="teacher1")
        self.kwargs['pk'] = 1
        response = ReviewSubmissionListView.as_view()(request, **self.kwargs)
        self.assertEqual(ReviewSubmission.objects.all().count(), 2)
        self.assertEqual(response.context_data['object_list'].count(), 2)
        self.assertContains(response, "student1")  # hacky
        self.assertContains(response, "student2")

        # student1 sees reviews of him by student2
        request = self.factory.get('/courses/prog1/F2018/submissions/r/1/list/?mode=my')
        request.user = self.s1
        self.kwargs['pk'] = 1
        response = ReviewSubmissionListView.as_view()(request, **self.kwargs)
        self.assertEqual(ReviewSubmission.objects.all().count(), 2)
        self.assertEqual(response.context_data['object_list'].count(), 1)
        self.assertEqual(response.context_data['object_list'][0].submitter_user, self.s2)

        # student2 sees reviews of him by student1
        request = self.factory.get('/courses/prog1/F2018/submissions/r/1/list/?mode=my')
        request.user = self.s2
        self.kwargs['pk'] = 1
        response = ReviewSubmissionListView.as_view()(request, **self.kwargs)
        self.assertEqual(ReviewSubmission.objects.all().count(), 2)
        self.assertEqual(response.context_data['object_list'].count(), 1)
        self.assertEqual(response.context_data['object_list'][0].submitter_user, self.s1)

        # if RE.show_reviews_only_to_teacher, nothing in the list
        rev_exercise.show_reviews_only_to_teacher = True
        rev_exercise.save()

        request = self.factory.get('/courses/prog1/F2018/submissions/r/1/list/?mode=my')
        request.user = self.s2
        self.kwargs['pk'] = 1
        response = ReviewSubmissionListView.as_view()(request, **self.kwargs)
        self.assertEqual(response.context_data['object_list'].count(), 0)
        self.assertContains(response, 'will only be visible')

        rev_exercise.show_reviews_only_to_teacher = False
        rev_exercise.save()

        # reviews by student missing
        rev_exercise.min_submission_count = 100
        rev_exercise.save()

        request = self.factory.get('/courses/prog1/F2018/submissions/r/1/list/?mode=my')
        request.user = self.s2
        self.kwargs['pk'] = 1
        response = ReviewSubmissionListView.as_view()(request, **self.kwargs)
        self.assertEqual(response.context_data['object_list'].count(), 0)
        self.assertContains(response, 'available after completing')

        # available in the future -> students should not see anything
        rev_exercise.min_submission_count = 0
        rev_exercise.show_reviews_after_date = timezone.now() + datetime.timedelta(days=1)
        rev_exercise.save()

        request = self.factory.get('/courses/prog1/F2018/submissions/r/1/list/?mode=my')
        request.user = self.s2
        self.kwargs['pk'] = 1
        response = ReviewSubmissionListView.as_view()(request, **self.kwargs)
        self.assertEqual(response.context_data['object_list'].count(), 0)
        self.assertContains(response, 'will be available after')

    def test_reviewsubmission_detail_answers(self):

        sub_exercise = SubmissionExercise.objects.get(name='T1 TEXT')
        rev_exercise = ReviewExercise.objects.get(name='T1 TEXT REVIEW')
        rev_exercise.question_order += [3]
        rev_exercise.save()

        for user in self.students[:2]:
            OriginalSubmission(course=self.course, submitter_user=user, exercise=sub_exercise, text="jadajada").save()

        rs_objects = []

        temp_file = SimpleUploadedFile(name='lorem_ipsum.txt', content=bytearray('jada jada', 'utf-8'))
        for user in self.students[:2]:
            reviewed_sub = OriginalSubmission.objects.filter(exercise=sub_exercise) \
                .exclude(submitter_user=user).first()
            rs = ReviewSubmission.objects.create(course=self.course, submitter_user=user,
                                                 exercise=rev_exercise, reviewed_submission=reviewed_sub)
            rs_objects.append(rs)
            Answer(submission=rs, value_text="juupase juu", question=Question.objects.get(pk=1)).save()
            Answer(submission=rs, value_choice="1", question=Question.objects.get(pk=2)).save()
            Answer(submission=rs, uploaded_file=temp_file, question=Question.objects.get(pk=3)).save()

        # teacher sees all reviews
        request = self.factory.get('/courses/prog1/F2018/submissions/r/1/1/')
        request.user = User.objects.get(username="teacher1")
        self.kwargs['pk'] = rev_exercise.pk
        self.kwargs['sub_pk'] = rs_objects[0].pk
        response = ReviewSubmissionDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "juupase juu")
        self.assertContains(response, "Score the work")

        # student sees hidden answer *given* by him
        request = self.factory.get('/courses/prog1/F2018/submissions/r/1/1/')
        request.user = self.s1
        self.kwargs['pk'] = rev_exercise.pk
        self.kwargs['sub_pk'] = rs_objects[0].pk
        response = ReviewSubmissionDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "juupase juu")
        self.assertContains(response, "Score the work")

        # student cannot see answer to a hidden question
        request = self.factory.get('/courses/prog1/F2018/submissions/r/1/1/')
        request.user = self.s2
        self.kwargs['pk'] = rev_exercise.pk
        self.kwargs['sub_pk'] = rs_objects[0].pk
        response = ReviewSubmissionDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "juupase juu")
        self.assertNotContains(response, "Score the work")

    def test_reviewsubmission_detail_permissions(self):

        sub_exercise = SubmissionExercise.objects.get(name='T1 TEXT')
        rev_exercise = ReviewExercise.objects.get(name='T1 TEXT REVIEW')
        rev_exercise.question_order += [3]
        rev_exercise.save()

        for user in self.students[:2]:
            OriginalSubmission(course=self.course, submitter_user=user, exercise=sub_exercise, text="jadajada").save()

        rs_objects = []

        temp_file = SimpleUploadedFile(name='lorem_ipsum.txt', content=bytearray('jada jada', 'utf-8'))
        for user in self.students[:2]:
            reviewed_sub = OriginalSubmission.objects.filter(exercise=sub_exercise) \
                .exclude(submitter_user=user).first()
            rs = ReviewSubmission.objects.create(course=self.course, submitter_user=user,
                                                 exercise=rev_exercise, reviewed_submission=reviewed_sub)
            rs_objects.append(rs)
            Answer(submission=rs, value_text="juupase juu", question=Question.objects.get(pk=1)).save()
            Answer(submission=rs, value_choice="1", question=Question.objects.get(pk=2)).save()
            Answer(submission=rs, uploaded_file=temp_file, question=Question.objects.get(pk=3)).save()

        request = self.factory.get('/courses/prog1/F2018/submissions/r/1/1/')
        request.user = self.s2
        self.kwargs['pk'] = rev_exercise.pk
        self.kwargs['sub_pk'] = rs_objects[0].pk

        # student cannot view feedback if available date in the future
        rev_exercise.show_reviews_after_date = timezone.now() + timezone.timedelta(hours=1)
        rev_exercise.save()
        self.assertRaises(PermissionDenied,
                          ReviewSubmissionDetailView.as_view(), request, **self.kwargs)
        rev_exercise.show_reviews_after_date = None
        rev_exercise.save()
        self.assertEqual(ReviewSubmissionDetailView.as_view()(request, **self.kwargs).status_code, 200)

        # student cannot view feedback if requirements not met
        rev_exercise.min_submission_count = 999
        rev_exercise.save()
        self.assertRaises(PermissionDenied,
                          ReviewSubmissionDetailView.as_view(), request, **self.kwargs)
        rev_exercise.min_submission_count = 0
        rev_exercise.save()
        self.assertEqual(ReviewSubmissionDetailView.as_view()(request, **self.kwargs).status_code, 200)

        # receiver *and* owner (feedback to self) can access
        rev_exercise.show_reviews_after_date = timezone.now() + timezone.timedelta(hours=1)
        rev_exercise.save()
        rs_objects[0].submitter_user = self.s2
        rs_objects[0].save()
        rs_objects[0].reviewed_submission.submitter_user = self.s2
        rs_objects[0].reviewed_submission.save()
        self.assertEqual(ReviewSubmissionDetailView.as_view()(request, **self.kwargs).status_code, 200)
        rev_exercise.show_reviews_after_date = None
        rev_exercise.save()

        # third party cannot see anything
        request.user = self.s3
        self.assertRaises(PermissionDenied,
                          ReviewSubmissionDetailView.as_view(), request, **self.kwargs)

    def test_ReviewSubmissionDetail_shows_correct_info(self):

        sub_exercise = SubmissionExercise.objects.get(name='T1 TEXT')
        rev_exercise = ReviewExercise.objects.get(name='T1 TEXT REVIEW')

        for user in self.students:
            OriginalSubmission(course=self.course, submitter_user=user, exercise=sub_exercise, text="jadajada").save()

        reviewed = self.s2
        reviewer = self.s1
        reviewed_sub = OriginalSubmission.objects.get(exercise=sub_exercise, submitter_user=reviewed)
        rev_sub = ReviewSubmission.objects.create(course=self.course, submitter_user=reviewer,
                                                  exercise=rev_exercise, reviewed_submission=reviewed_sub)

        request = self.factory.get(rev_sub.get_absolute_url())
        self.kwargs['pk'] = rev_exercise.pk
        self.kwargs['sub_pk'] = rev_sub.pk

        rev_exercise.min_submission_count = 0  # so that receiver can view
        rev_exercise.type = ReviewExercise.RANDOM
        rev_exercise.save()

        request.user = self.t1
        response = ReviewSubmissionDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "<strong>Submitter")
        self.assertContains(response, "<strong>Reviewed submission")

        request.user = reviewer
        response = ReviewSubmissionDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "<strong>Submitter")
        self.assertNotContains(response, "<strong>Reviewed")

        request.user = reviewed
        response = ReviewSubmissionDetailView.as_view()(request, **self.kwargs)
        self.assertNotContains(response, "<strong>Submitter")
        self.assertContains(response, "<strong>Reviewed submission")

        rev_exercise.type = ReviewExercise.CHOOSE
        rev_exercise.save()

        request.user = self.t1
        response = ReviewSubmissionDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "<strong>Submitter")
        self.assertContains(response, "<strong>Reviewed submission")

        request.user = reviewer
        response = ReviewSubmissionDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "<strong>Submitter")
        self.assertNotContains(response, "<strong>Reviewed submission")
        self.assertContains(response, "<strong>Reviewed student")

        request.user = reviewed
        response = ReviewSubmissionDetailView.as_view()(request, **self.kwargs)
        self.assertNotContains(response, "<strong>Submitter")
        self.assertContains(response, "<strong>Reviewed submission")
        self.assertNotContains(response, "<strong>Reviewed student")

        rev_exercise.type = ReviewExercise.GROUP
        rev_exercise.save()

        request.user = self.t1
        response = ReviewSubmissionDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "<strong>Submitter")
        self.assertContains(response, "<strong>Reviewed student")

        request.user = reviewer
        response = ReviewSubmissionDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "<strong>Submitter")
        self.assertNotContains(response, "<strong>Reviewed submission")
        self.assertContains(response, "<strong>Reviewed student")

        request.user = reviewed
        response = ReviewSubmissionDetailView.as_view()(request, **self.kwargs)
        self.assertNotContains(response, "<strong>Submitter")
        self.assertNotContains(response, "<strong>Reviewed submission")
        self.assertNotContains(response, "<strong>Reviewed student")

    def test_student_cannot_download_submission_not_owned(self):
        exercise = SubmissionExercise.objects.get(pk=1)

        exercise.type = 'FILE_UPLOAD'
        exercise.accepted_filetypes = '.txt'
        exercise.save()

        temp_file = SimpleUploadedFile(name='lorem_ipsum.txt', content=bytearray('jada jada', 'utf-8'))
        sub = OriginalSubmission(course=self.course, file=temp_file, submitter_user=self.s1, exercise=exercise)
        sub.save()

        request = self.factory.get(f'/courses/prog1/F2018/submissions/download/{sub.pk}/')
        request.user = self.s2
        self.kwargs['pk'] = sub.pk

        self.assertRaises(PermissionDenied,
                          DownloadSubmissionView.as_view(), request, **self.kwargs)

    def test_student_can_download_submission(self):
        exercise = SubmissionExercise.objects.get(pk=1)

        group = StudentGroup(name="g-1", student_usernames=[self.s1.email, self.s2.email], course=self.course)
        group.save()

        exercise.type = 'FILE_UPLOAD'
        exercise.accepted_filetypes = '.txt'
        exercise.save()

        temp_file = SimpleUploadedFile(name='lorem_ipsum.txt', content=bytearray('jada jada', 'utf-8'))
        sub = OriginalSubmission(course=self.course, file=temp_file, submitter_user=self.s1, submitter_group=group,
                                 exercise=exercise)
        sub.save()

        for user, code in [(self.s1, 200), (self.s2, 200), (self.s3, 403)]:
            request = self.factory.get(f'/courses/prog1/F2018/submissions/download/{sub.pk}/')
            request.user = user
            self.kwargs['pk'] = sub.pk

            if code == 403:
                self.assertRaises(PermissionDenied,
                                  DownloadSubmissionView.as_view(), request, **self.kwargs)
            else:
                response = DownloadSubmissionView.as_view()(request, **self.kwargs)
                self.assertEqual(response.status_code, code)

    def test_download_tokens_allow_downloading(self):

        exercise = SubmissionExercise.objects.get(pk=1)
        exercise.type = 'FILE_UPLOAD'
        exercise.accepted_filetypes = '.txt'
        exercise.save()

        temp_file = SimpleUploadedFile(name='lorem_ipsum.txt', content=bytearray('jada jada', 'utf-8'))
        sub = OriginalSubmission(course=self.course, file=temp_file, submitter_user=self.s1,
                                 exercise=exercise)
        sub.save()

        rev = ReviewSubmission(course=self.course,
                               submitter_user=self.s1,
                               exercise=exercise.review_exercise,
                               reviewed_submission=sub)
        rev.save()

        answer_with_file = Answer(
            question=Question.objects.get(pk=3),
            submission=rev,
            uploaded_file=temp_file,
        )
        answer_with_file.save()

        view_request = self.factory.get(exercise.get_absolute_url() + "?some=queryparams")
        osub_token = sub.get_download_token_for(self.s1, view_request)
        view_request = self.factory.get(exercise.review_exercise.get_absolute_url() + "?some=queryparams")
        rsub_token = rev.get_download_token_for(self.s1, view_request)

        cases = [
            (AnonymousUser, 403, sub, ""),
            (AnonymousUser, 200, sub, f"?dl_token={osub_token}"),
            (AnonymousUser, 403, sub, f"?dl_token={osub_token}_THIS_SHOULD_CAUSE_PROBLEMS"),
            (AnonymousUser, 403, answer_with_file, ""),
            (AnonymousUser, 200, answer_with_file, f"&dl_token={rsub_token}"),
            (AnonymousUser, 403, answer_with_file, f"&dl_token={rsub_token}_THIS_SHOULD_CAUSE_PROBLEMS"),
        ]

        for user, code, sub, query in cases:
            url = f"{sub.get_file_download_url()}{query}"
            request = self.factory.get(url)
            request.user = user
            self.kwargs['pk'] = sub.pk

            if code == 403:
                self.assertRaises(PermissionDenied,
                                  DownloadSubmissionView.as_view(), request, **self.kwargs)
            else:
                response = DownloadSubmissionView.as_view()(request, **self.kwargs)
                self.assertEqual(response.status_code, code)

        DownloadToken.objects.all().delete()

        for user, _, sub, query in cases:
            url = f"{sub.get_file_download_url()}{query}"
            request = self.factory.get(url)
            request.user = user
            self.kwargs['pk'] = sub.pk
            self.assertRaises(PermissionDenied,
                              DownloadSubmissionView.as_view(), request, **self.kwargs)

    def test_student_can_download_via_reviewlock(self):
        exercise = SubmissionExercise.objects.get(pk=1)

        exercise.type = 'FILE_UPLOAD'
        exercise.accepted_filetypes = '.txt'
        exercise.save()

        temp_file = SimpleUploadedFile(name='lorem_ipsum.txt', content=bytearray('jada jada', 'utf-8'))
        sub = OriginalSubmission(course=self.course, file=temp_file, submitter_user=self.s1,
                                 exercise=exercise)
        sub.save()

        re = ReviewExercise.objects.get(pk=1)
        re.type = ReviewExercise.RANDOM
        re.save()

        rlock = ReviewLock(user=self.s2, original_submission=sub, review_exercise=re, review_submission=None)
        rlock.save()

        # user with reviewlock can download
        request = self.factory.get(f'/courses/prog1/F2018/submissions/download/{sub.pk}/')
        request.user = self.s2
        self.kwargs['pk'] = sub.pk
        response = DownloadSubmissionView.as_view()(request, **self.kwargs)
        self.assertEqual(response.status_code, 200)

        re.use_groups = True
        re.save()
        group = StudentGroup(name="g-1", student_usernames=[self.s2.email, self.s3.email], course=self.course)
        group.save()
        rlock.group = group
        rlock.save()

        # user in a group that has a reviewlock can download
        request = self.factory.get(f'/courses/prog1/F2018/submissions/download/{sub.pk}/')
        request.user = self.s3
        self.kwargs['pk'] = sub.pk
        response = DownloadSubmissionView.as_view()(request, **self.kwargs)
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_download_answer_file_not_owned(self):
        s_exercise = SubmissionExercise.objects.get(name="T1 TEXT")
        r_exercise = ReviewExercise.objects.get(name="T1 TEXT REVIEW")

        sub = OriginalSubmission(course=self.course, text="juups", submitter_user=self.s1, exercise=s_exercise)
        sub.save()

        r_exercise.question_order = ['3']
        r_exercise.save()

        rev_sub = ReviewSubmission(course=self.course, reviewed_submission=sub,
                                   submitter_user=self.s2, exercise=r_exercise)
        rev_sub.save()

        temp_file = SimpleUploadedFile(name='lorem_ipsum.txt', content=bytearray('jada jada', 'utf-8'))

        answer_with_file = Answer(
            question=Question.objects.get(pk=3),
            submission=rev_sub,
            uploaded_file=temp_file,
        )
        answer_with_file.save()

        request = self.factory.get(f'/courses/prog1/F2018/submissions/download/{answer_with_file.pk}/?type=answer')
        request.user = self.s3
        self.kwargs['pk'] = answer_with_file.pk

        self.assertRaises(PermissionDenied,
                          DownloadSubmissionView.as_view(), request, **self.kwargs)

        g = StudentGroup(name="g1", course=self.course, student_usernames=[self.s1.email, self.s3.email])
        g.save()
        sub.submitter_group = g
        sub.save()

        for user in self.students + [self.t1]:
            request = self.factory.get(f'/courses/prog1/F2018/submissions/download/{answer_with_file.pk}/?type=answer')
            request.user = user
            self.kwargs['pk'] = answer_with_file.pk

            if user == self.s4:
                self.assertRaises(PermissionDenied,
                                  DownloadSubmissionView.as_view(), request, **self.kwargs)
            else:
                response = DownloadSubmissionView.as_view()(request, **self.kwargs)
                self.assertEqual(response.status_code, 200)

    def test_student_cannot_download_hide_from_receiver_answer_file(self):
        s_exercise = SubmissionExercise.objects.get(name="T1 TEXT")
        r_exercise = ReviewExercise.objects.get(name="T1 TEXT REVIEW")

        sub = OriginalSubmission(course=self.course, text="juups", submitter_user=self.s1, exercise=s_exercise)
        sub.save()

        r_exercise.question_order = ['3']
        r_exercise.save()

        rev_sub = ReviewSubmission(course=self.course, reviewed_submission=sub,
                                   submitter_user=self.s2, exercise=r_exercise)
        rev_sub.save()

        temp_file = SimpleUploadedFile(name='lorem_ipsum.txt', content=bytearray('jada jada', 'utf-8'))
        question = Question.objects.get(pk=3)

        answer_with_file = Answer(
            question=question,
            submission=rev_sub,
            uploaded_file=temp_file,
        )
        answer_with_file.save()

        request = self.factory.get(f'/courses/prog1/F2018/submissions/download/{answer_with_file.pk}/?type=answer')
        request.user = self.s1
        self.kwargs['pk'] = answer_with_file.pk

        self.assertEqual(DownloadSubmissionView.as_view()(request, **self.kwargs).status_code, 200)
        question.hide_from_receiver = True
        question.save()
        self.assertRaises(PermissionDenied,
                          DownloadSubmissionView.as_view(), request, **self.kwargs)

    def test_original_submission_delete_confirmation_page_shows_cascades(self):

        os = OriginalSubmission(
            course=self.course,
            exercise=SubmissionExercise.objects.get(name="T1 TEXT"),
            submitter_user=self.s1,
            text="jada jada jada jada",
        )
        os.save()

        request = self.factory.get(os.get_delete_url())
        self.kwargs['pk'] = os.exercise.pk
        self.kwargs['sub_pk'] = os.pk
        request.user = self.s1

        # students cannot access
        self.assertRaises(PermissionDenied,
                          OriginalSubmissionDeleteView.as_view(), request, **self.kwargs)

        request.user = self.t1
        response = OriginalSubmissionDeleteView.as_view()(request, **self.kwargs)
        self.assertContains(response, "No peer-reviews exist yet")

        res = []
        for s in [self.s2, self.s3]:
            re = ReviewSubmission(
                course=self.course,
                exercise=ReviewExercise.objects.get(name="T1 TEXT REVIEW"),
                reviewed_submission=os,
                submitter_user=s,
            )
            re.save()
            res.append(re)

        response = OriginalSubmissionDeleteView.as_view()(request, **self.kwargs)
        self.assertNotContains(response, "No peer-reviews exist yet")
        # -> is turned into -&gt; in the response -> just replace that when looking for
        self.assertContains(response, str(res[0]).replace(">", "&gt;"))
        self.assertContains(response, str(res[1]).replace(">", "&gt;"))

        self.assertEqual(OriginalSubmission.objects.count(), 1)
        self.assertEqual(ReviewSubmission.objects.count(), 2)

        request = self.factory.get(res[0].get_delete_url())
        self.kwargs['pk'] = res[0].exercise.pk
        self.kwargs['sub_pk'] = res[0].pk
        request.user = self.s1

        # students cannot access
        self.assertRaises(PermissionDenied,
                          ReviewSubmissionDeleteView.as_view(), request, **self.kwargs)

        # delete page doesn't list any useful information, no need to check

        os.delete()

        self.assertEqual(OriginalSubmission.objects.count(), 0)
        self.assertEqual(ReviewSubmission.objects.count(), 0)
