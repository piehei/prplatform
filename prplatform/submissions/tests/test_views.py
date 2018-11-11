from django.test import RequestFactory, TestCase
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied

import datetime

from prplatform.users.models import User, StudentGroup
from prplatform.courses.models import Course
from prplatform.exercises.models import SubmissionExercise, ReviewExercise
from prplatform.exercises.question_models import Question

from prplatform.submissions.models import OriginalSubmission, ReviewSubmission, Answer
from prplatform.submissions.views import OriginalSubmissionListView, DownloadSubmissionView, \
                                         ReviewSubmissionListView, ReviewSubmissionDetailView


class SubmissionsTest(TestCase):
    fixtures = ["courses.yaml"]

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.kwargs = {'base_url_slug': 'prog1', 'url_slug': 'F2018'}

    def test_studentCanOnlyViewPersonalSubmissions(self):

        exercise = SubmissionExercise.objects.get(pk=1)
        course = Course.objects.get(pk=1)

        for username in ["student1", "student2", "student3"]:
            user = User.objects.get(username=username)
            OriginalSubmission(course=course, submitter_user=user, exercise=exercise, text="jadajada").save()

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

        g1 = StudentGroup.objects.create(course=course, name='group1', student_usernames=['student1@prp.fi', 'student2@prp.fi'])
        g2 = StudentGroup.objects.create(course=course, name='group2', student_usernames=['student3@prp.fi'])

        exercise.use_groups = True
        exercise.save()

        OriginalSubmission(course=course, exercise=exercise, text='jada jada',
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

        OriginalSubmission(course=course, exercise=exercise, text='jada jada',
                           submitter_user=User.objects.get(username='student2'),
                           submitter_group=g1).save()

        OriginalSubmission(course=course, exercise=exercise, text='jada jada',
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
        OriginalSubmission(course=course, exercise=exercise, text='jada jada',
                           submitter_user=User.objects.get(username='student2'),
                           ).save()
        OriginalSubmission(course=course, exercise=exercise, text='jada jada',
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
        course = Course.objects.get(pk=1)

        for username in ["student1", "student2", "student3", "teacher1"]:
            user = User.objects.get(username=username)
            OriginalSubmission(course=course, submitter_user=user, exercise=exercise, text="jadajada").save()

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
        course = Course.objects.get(pk=1)

        users = [
            User.objects.get(username="student1"),
            User.objects.get(username="student2")
        ]

        for user in users:
            OriginalSubmission(course=course, submitter_user=user, exercise=sub_exercise, text="jadajada").save()

        for user in users:
            revsub = OriginalSubmission.objects.filter(exercise=sub_exercise) \
                                                            .exclude(submitter_user=user).first()
            ReviewSubmission(course=course, submitter_user=user,
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
        request.user = users[0]
        self.kwargs['pk'] = 1
        response = ReviewSubmissionListView.as_view()(request, **self.kwargs)
        self.assertEqual(ReviewSubmission.objects.all().count(), 2)
        self.assertEqual(response.context_data['object_list'].count(), 1)
        self.assertEqual(response.context_data['object_list'][0].submitter_user, users[1])

        # student2 sees reviews of him by student1
        request = self.factory.get('/courses/prog1/F2018/submissions/r/1/list/?mode=my')
        request.user = users[1]
        self.kwargs['pk'] = 1
        response = ReviewSubmissionListView.as_view()(request, **self.kwargs)
        self.assertEqual(ReviewSubmission.objects.all().count(), 2)
        self.assertEqual(response.context_data['object_list'].count(), 1)
        self.assertEqual(response.context_data['object_list'][0].submitter_user, users[0])

        # reviews by student missing
        rev_exercise.minimum_reviews_per_student = 100
        rev_exercise.save()

        request = self.factory.get('/courses/prog1/F2018/submissions/r/1/list/?mode=my')
        request.user = users[1]
        self.kwargs['pk'] = 1
        response = ReviewSubmissionListView.as_view()(request, **self.kwargs)
        self.assertEqual(response.context_data['object_list'].count(), 0)
        self.assertContains(response, 'available after completing')

        # available in the future -> students should not see anything
        rev_exercise.minimum_reviews_per_student = 0
        rev_exercise.show_reviews_after_date = datetime.datetime.now() + datetime.timedelta(days=1)
        rev_exercise.save()

        request = self.factory.get('/courses/prog1/F2018/submissions/r/1/list/?mode=my')
        request.user = users[1]
        self.kwargs['pk'] = 1
        response = ReviewSubmissionListView.as_view()(request, **self.kwargs)
        self.assertEqual(response.context_data['object_list'].count(), 0)
        self.assertContains(response, 'will be available after')

    def test_ReviewSubPagePermissionsWork(self):

        sub_exercise = SubmissionExercise.objects.get(name='T1 TEXT')
        rev_exercise = ReviewExercise.objects.get(name='T1 TEXT REVIEW')
        course = Course.objects.get(pk=1)
        users = [
            User.objects.get(username="student1"),
            User.objects.get(username="student2")
        ]

        for user in users:
            OriginalSubmission(course=course, submitter_user=user, exercise=sub_exercise, text="jadajada").save()

        rs_objects = []

        for user in users:
            reviewed_sub = OriginalSubmission.objects.filter(exercise=sub_exercise) \
                                                            .exclude(submitter_user=user).first()
            rs = ReviewSubmission.objects.create(course=course, submitter_user=user,
                                                 exercise=rev_exercise, reviewed_submission=reviewed_sub)
            rs_objects.append(rs)
            Answer.objects.create(submission=rs, value_text="juupase juu", question=Question.objects.get(pk=1))
            Answer.objects.create(submission=rs, value_choice="1", question=Question.objects.get(pk=2))

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
        request.user = users[0]
        self.kwargs['pk'] = rev_exercise.pk
        self.kwargs['sub_pk'] = rs_objects[0].pk
        response = ReviewSubmissionDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "juupase juu")
        self.assertContains(response, "Score the work")

        # student cannot see answer to a hidden question
        request = self.factory.get('/courses/prog1/F2018/submissions/r/1/1/')
        request.user = users[1]
        self.kwargs['pk'] = rev_exercise.pk
        self.kwargs['sub_pk'] = rs_objects[0].pk
        response = ReviewSubmissionDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "juupase juu")
        self.assertNotContains(response, "Score the work")

    def test_student_cannot_load_code_not_owned(self):
        exercise = SubmissionExercise.objects.get(pk=1)
        course = Course.objects.get(pk=1)

        user1 = User.objects.get(username="student1")
        from django.core.files.uploadedfile import SimpleUploadedFile

        exercise.type = 'FILE_UPLOAD'
        exercise.accepted_filetypes = '.txt'
        exercise.save()

        tmpFile = SimpleUploadedFile(name='lorem_ipsum.txt', content=bytearray('jada jada', 'utf-8'))
        sub = OriginalSubmission(course=course, file=tmpFile, submitter_user=user1, exercise=exercise)
        sub.save()

        request = self.factory.get(f'/courses/prog1/F2018/submissions/download/{sub.pk}/')
        request.user = User.objects.get(username="student2")
        self.kwargs['pk'] = sub.pk

        self.assertRaises(PermissionDenied,
                          DownloadSubmissionView.as_view(), request, **self.kwargs)
