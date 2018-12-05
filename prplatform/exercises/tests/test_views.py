from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.test import RequestFactory, TestCase

import datetime

from prplatform.users.models import User, StudentGroup
from prplatform.courses.models import Course

from prplatform.submissions.models import OriginalSubmission, ReviewSubmission, ReviewLock
from prplatform.submissions.views import ReviewSubmissionListView
from prplatform.exercises.views import SubmissionExerciseCreateView, SubmissionExerciseDetailView, \
                                       ReviewExerciseDetailView
from prplatform.exercises.models import SubmissionExercise, ReviewExercise
from prplatform.exercises.deviation_models import SubmissionExerciseDeviation


def add_middleware(request, middleware_class):
    middleware = middleware_class()
    middleware.process_request(request)
    return request


class ExerciseTest(TestCase):
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

    ###
    #   SubmissionExerciseCreateView
    #   uses isTeacherMixin
    #

    def test_isTeacher_anon_raises(self):

        request = self.factory.get('/courses/prog1/F2018/exercises/s/1/')
        self.kwargs['pk'] = 1
        request.user = AnonymousUser()
        self.assertRaises(PermissionDenied,
                          SubmissionExerciseCreateView.as_view(), request, **self.kwargs)

        request.user = self.s1
        self.assertRaises(PermissionDenied,
                          SubmissionExerciseCreateView.as_view(), request, **self.kwargs)

        request.user = self.t1
        try:
            SubmissionExerciseCreateView.as_view()(request, **self.kwargs)
        except Exception:
            self.fail("Teacher should be allowed to access")

    def test_exerciseOpen(self):

        request = self.factory.get('/courses/prog1/F2018/exercises/s/1/')
        request.user = self.s1
        self.kwargs['pk'] = 1

        response = SubmissionExerciseDetailView.as_view()(request, **self.kwargs)

        self.assertNotContains(response, "This exercise is closed.")
        self.assertContains(response, "Submit")
        self.assertContains(response, "<form")

    def test_exerciseOpens(self):

        request = self.factory.get('/courses/prog1/F2018/exercises/s/4/')
        request.user = self.s1
        self.kwargs['pk'] = 4

        se = SubmissionExercise.objects.get(pk=4)
        se.opening_time = "2020-01-01 10:10"
        se.closing_time = "2021-01-01 10:10"
        se.save()

        response = SubmissionExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "This exercise will open on")
        self.assertEqual(response.context_data['disable_form'], True)

    def test_exerciseClosed(self):

        request = self.factory.get('/courses/prog1/F2018/exercises/s/4/')
        request.user = self.s1
        self.kwargs['pk'] = 4

        response = SubmissionExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "This exercise was closed on")
        self.assertEqual(response.context_data['disable_form'], True)

    def test_deadlineExtensionAllowsSubmitting(self):

        request = self.factory.get('/courses/prog1/F2018/exercises/s/4/')
        request.user = self.s1
        self.kwargs['pk'] = 4

        se = SubmissionExercise.objects.get(pk=4)
        se.opening_time = "2005-01-01 10:10"
        se.closing_time = "2006-01-01 10:10"
        se.save()

        response = SubmissionExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "This exercise was closed on")
        self.assertEqual(response.context_data['disable_form'], True)

        # student *SHOULD* have an extension
        extension = SubmissionExerciseDeviation(exercise=se, user=self.s1,
                                                new_deadline=datetime.datetime(2050, 1, 1))
        extension.save()

        response = SubmissionExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "This exercise was closed on")
        self.assertContains(response, "However, you have an extended deadline until")
        self.assertEqual(response.context_data['disable_form'], False)

        # student *SHOULD NOT* have an extension
        extension.new_deadline = "2006-01-01 10:10"
        extension.save()

        response = SubmissionExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "This exercise was closed on")
        self.assertNotContains(response, "However, you have an extended deadline until")
        self.assertEqual(response.context_data['disable_form'], True)

    def test_studentCanSubmit(self):

        request = self.factory.post('/courses/prog1/F2018/exercises/s/1/', {'text': 'Submitted text'})
        request.user = self.s1
        self.kwargs['pk'] = 1

        request = add_middleware(request, SessionMiddleware)
        request = add_middleware(request, MessageMiddleware)

        response = SubmissionExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertEqual(response.status_code, 302)

    def test_studentCannotSubmitMultipleTimes(self):

        # first create a submission by a student
        s_exercise = SubmissionExercise.objects.get(pk=1)
        course = Course.objects.get(pk=1)
        orig_sub_user1 = OriginalSubmission(course=course, submitter_user=self.s1, exercise=s_exercise, text="jadajada")
        orig_sub_user1.save()
        # then load the page and check it disables second submission
        request = self.factory.get('/courses/prog1/F2018/exercises/s/1/')
        request.user = self.s1
        self.kwargs['pk'] = 1

        response = SubmissionExerciseDetailView.as_view()(request, **self.kwargs)

        self.assertContains(response, "You have reached the maximum number of submissions")
        self.assertEqual(response.context_data['disable_form'], True)

        OriginalSubmission(course=course, submitter_user=self.s2, exercise=s_exercise, text="juuh").save()
        r_exercise = ReviewExercise.objects.get(reviewable_exercise=s_exercise)
        request = self.factory.get('/courses/prog1/F2018/exercises/r/1/')
        request.user = self.s2
        self.kwargs['pk'] = 1
        response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "jadajada")
        self.assertEqual(ReviewLock.objects.all().count(), 1)
        rsub = ReviewSubmission(course=course, exercise=r_exercise, submitter_user=self.s2,
                                reviewed_submission=orig_sub_user1)
        rsub.save()
        rlock = ReviewLock.objects.first()
        rlock.review_submission = rsub
        rlock.save()
        request = self.factory.get('/courses/prog1/F2018/exercises/r/1/')
        request.user = self.s2
        self.kwargs['pk'] = 1
        response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, 'You have already submitted your peer-reviews to this exercise.')

    def test_teacherCanSubmitMultipleTimes(self):

        exercise = SubmissionExercise.objects.get(pk=1)
        course = Course.objects.get(pk=1)
        OriginalSubmission(course=course, submitter_user=self.t1, exercise=exercise, text="jadajada").save()
        OriginalSubmission(course=course, submitter_user=self.t1, exercise=exercise, text="jadajada").save()
        OriginalSubmission(course=course, submitter_user=self.t1, exercise=exercise, text="jadajada").save()

        request = self.factory.get('/courses/prog1/F2018/exercises/s/1/')
        request.user = self.t1
        self.kwargs['pk'] = 1

        response = SubmissionExerciseDetailView.as_view()(request, **self.kwargs)

        self.assertNotContains(response, "You have reached the maximum number of submissions")
        self.assertContains(response, "Submit")

    def test_submissionStatesWork(self):

        exercise = SubmissionExercise.objects.get(name='T5 STATE')
        course = Course.objects.get(pk=1)

        subs = []
        for s in self.students[:2]:
            sub = OriginalSubmission(course=course, submitter_user=s, state='submitted', exercise=exercise,
                                     text=f"answer by {s.username}")
            sub.save()
            subs.append(sub)

        # submissions used
        request = self.factory.get('/courses/prog1/F2018/exercises/s/5/')
        request.user = self.s1
        self.kwargs['pk'] = 5
        response = SubmissionExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "You have reached the maximum number of submissions")

        subs[0].state = OriginalSubmission.BOOMERANG
        subs[0].save()

        # can submit when BOOMERANG
        request = self.factory.get('/courses/prog1/F2018/exercises/s/5/')
        request.user = self.s1
        self.kwargs['pk'] = 5
        response = SubmissionExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertNotContains(response, "You have reached the maximum number of submissions")

        # cannot peer-review while BOOMERANG
        r_exer = ReviewExercise.objects.get(name='T5 STATE REVIEW')
        request = self.factory.get(r_exer.get_absolute_url())
        request.user = self.s1
        self.kwargs['pk'] = r_exer.pk
        response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "You cannot make peer-reviews before")

        subs[1].state = OriginalSubmission.READY_FOR_REVIEW
        subs[1].save()

        # only READY_FOR_REVIEW is available for review
        r_exer = ReviewExercise.objects.get(name='T5 STATE REVIEW')
        request = self.factory.get(r_exer.get_absolute_url())
        request.user = self.s2
        self.kwargs['pk'] = r_exer.pk
        response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "Not a thing was found")

        subs[0].state = OriginalSubmission.READY_FOR_REVIEW
        subs[0].save()

        r_exer = ReviewExercise.objects.get(name='T5 STATE REVIEW')
        request = self.factory.get(r_exer.get_absolute_url())
        request.user = self.s1
        self.kwargs['pk'] = r_exer.pk
        response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "answer by student2")
        self.assertEqual(ReviewLock.objects.count(), 1)

    def test_group_peer_review(self):

        se = SubmissionExercise.objects.get(name="T1 TEXT")
        re = ReviewExercise.objects.get(name="T1 TEXT REVIEW")

        se.type = SubmissionExercise.GROUP_NO_SUBMISSION
        se.save()

        re.type = ReviewExercise.GROUP
        re.use_groups = True
        re.save()

        g = StudentGroup(course=se.course,
                         name="g1",
                         student_usernames=[self.s1.email, self.s2.email, "temp-test@temp-test.com"]
                         )
        g.save()

        user_count_before = User.objects.all().count()
        self.assertEqual(0, se.submissions.count())

        request = self.factory.get(re.get_absolute_url())
        request.user = self.s1
        self.kwargs['pk'] = re.pk
        ReviewExerciseDetailView.as_view()(request, **self.kwargs)

        # should create temp user for temp-test@temp-test.com
        self.assertEqual(user_count_before + 1, User.objects.all().count())
        # should have three orig subs because three group members
        self.assertEqual(3, se.submissions.count())

        temp_email = "temp-test@temp-test.com"
        temp_user = User.objects.get(email=temp_email)
        self.assertEqual(temp_user.temporary, True)

        request.user = self.s2
        ReviewExerciseDetailView.as_view()(request, **self.kwargs)

        # page load as another group member shouldn't affect these
        self.assertEqual(user_count_before + 1, User.objects.all().count())
        self.assertEqual(3, se.submissions.count())

        orig_subs_for_temp_user = OriginalSubmission.objects.filter(submitter_user=temp_user)
        self.assertEqual(1, orig_subs_for_temp_user.count())

        resub = ReviewSubmission(
                    course=re.course,
                    exercise=re,
                    submitter_user=self.s1,
                    reviewed_submission=orig_subs_for_temp_user.first(),
                )
        resub.save()

        # create actual user, this basically simulates sihbboleth login in a future time
        actual_user = User.objects.create(username="actual_user",
                                          email=temp_email,
                                          password="actual_passwd")

        self.assertEqual(2, User.objects.filter(email=temp_email).count())

        orig_submitter = OriginalSubmission.objects.get(submitter_user__email=temp_email).submitter_user.username

        # login the actual user
        # this triggers users/receivers.py which will:
        #   - find all submissions done with a temp user using same email
        #   - transfer all submissions to this actual user
        #   - delete temp user

        self.client.force_login(actual_user)

        actual_submitter = OriginalSubmission.objects.get(submitter_user__email=temp_email).submitter_user.username
        self.assertNotEqual(orig_submitter, actual_submitter)

        self.assertEqual(1, User.objects.filter(email=temp_email).count())
        actual_user = User.objects.get(email=temp_email)
        self.assertEqual(actual_user.temporary, False)

        request.user = actual_user
        response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)

        self.assertEqual(user_count_before + 1, User.objects.all().count())
        self.assertEqual(3, se.submissions.count())

        # nothing, student1, student2
        self.assertEqual(str(response.context_data['chooseForm']).count("<option"), 3)

        re.can_review_own_submission = True
        re.save()

        response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)

        # nothing, student1, student2, actual_user
        self.assertEqual(str(response.context_data['chooseForm']).count("<option"), 4)

        # actual_user can see one review by another student (student1)
        request = self.factory.get(re.get_list_url())
        request.user = actual_user
        self.kwargs['pk'] = re.pk
        response = ReviewSubmissionListView.as_view()(request, **self.kwargs)
        self.assertEqual(response.context_data['reviewsubmission_list'].count(), 1)


