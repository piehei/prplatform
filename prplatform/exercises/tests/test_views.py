from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.test import RequestFactory, TestCase
from django.http import HttpRequest
from django.urls import resolve

from django.utils import timezone

import datetime
import pytz

from prplatform.users.models import (
    StudentGroup,
    User,
)
from prplatform.users.receivers import change_original_submission_submitters
from prplatform.courses.models import Course
from prplatform.submissions.models import (
    OriginalSubmission,
    ReviewSubmission,
)
from prplatform.submissions.reviewlock_models import ReviewLock
from prplatform.submissions.views import ReviewSubmissionListView
from prplatform.exercises.views import (
    SubmissionExerciseCreateView,
    SubmissionExerciseDetailView,
    ReviewExerciseDetailView,
)
from prplatform.exercises.models import (
    ReviewExercise,
    SubmissionExercise,
)
from prplatform.exercises.deviation_models import SubmissionExerciseDeviation


def add_middleware(request, middleware_class):
    middleware = middleware_class()
    middleware.process_request(request)
    return request


def add_required_middlewares(request):
    request = add_middleware(request, SessionMiddleware)
    request = add_middleware(request, MessageMiddleware)
    # this is for LtiLoginMiddleware
    # TODO: should this be refactored somehow?
    request.LTI_MODE = False
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
        self.s5 = User.objects.get(username="student5")
        self.s6 = User.objects.get(username="student6")

        # dont add s5 and s6 here since tests were written before they existed
        self.students = [self.s1, self.s2, self.s3, self.s4]

        self.t1 = User.objects.get(username="teacher1")
        self.course = Course.objects.get(pk=1)

        self.SE1 = SubmissionExercise.objects.get(name='T1 TEXT')
        self.RE1 = ReviewExercise.objects.get(name='T1 TEXT REVIEW')

    def get(self, exercise, user, lti=False):
        request = self.factory.get(exercise.get_absolute_url())
        request.user = user
        request.LTI_MODE = lti
        self.kwargs['pk'] = exercise.pk
        views = {
            'SubmissionExercise': SubmissionExerciseDetailView,
            'ReviewExercise': ReviewExerciseDetailView,
        }
        name = exercise.__class__.__name__
        return views[name].as_view()(request, **self.kwargs)

    def post(self, exercise, user, payload):
        request = self.factory.post(exercise.get_absolute_url(), payload)
        request.user = user
        self.kwargs['pk'] = exercise.pk
        request = add_required_middlewares(request)
        views = {
            'SubmissionExercise': SubmissionExerciseDetailView,
            'ReviewExercise': ReviewExerciseDetailView,
        }
        name = exercise.__class__.__name__
        return views[name].as_view()(request, **self.kwargs)

    def create_originalsubmission_for(self, exercise, users):
        if type(users) is not list:
            users = [users]

        submissions = []
        for user in users:
            sub = OriginalSubmission(course=self.course,
                                     submitter_user=user,
                                     exercise=exercise,
                                     text=f"text by {user}")
            sub.save()
            submissions.append(sub)
        return submissions

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

    def test_submit_as_student(self):
        # only teacher should see
        for ex in [self.SE1, self.RE1]:
            self.assertNotContains(self.get(ex, self.s1), ex.get_submit_as_student_url())
            self.assertContains(self.get(ex, self.t1), ex.get_submit_as_student_url())

        # in lti mode no one should see
        for ex in [self.SE1, self.RE1]:
            self.assertNotContains(self.get(ex, self.s1, lti=True), ex.get_submit_as_student_url())
            self.assertNotContains(self.get(ex, self.t1, lti=True), ex.get_submit_as_student_url())

    def test_exercise_open(self):
        res = self.get(self.SE1, self.s1)
        self.assertNotContains(res, "This exercise is closed.")
        self.assertContains(res, "Submit")
        self.assertContains(res, "<form")

    def test_exercise_will_open(self):

        self.SE1.opening_time = timezone.now()+timezone.timedelta(hours=1)
        self.SE1.closing_time = timezone.now()+timezone.timedelta(hours=2)
        self.SE1.save()
        res = self.get(self.SE1, self.s1)
        self.assertContains(res, "This exercise will open on")
        self.assertEqual(res.context_data['disable_form'], True)

    def test_exercise_closed(self):
        self.SE1.opening_time = timezone.now()-timezone.timedelta(hours=2)
        self.SE1.closing_time = timezone.now()-timezone.timedelta(hours=1)
        self.SE1.save()
        res = self.get(self.SE1, self.s1)
        self.assertContains(res, "This exercise was closed on")
        self.assertEqual(res.context_data['disable_form'], True)

    def test_deadline_extension_allows_submitting(self):

        self.SE1.opening_time = "2005-01-01 10:10+03:00"
        self.SE1.closing_time = "2006-01-01 10:10+03:00"
        self.SE1.save()

        res = self.get(self.SE1, self.s1)
        self.assertContains(res, "This exercise was closed on")
        self.assertEqual(res.context_data['disable_form'], True)

        # student *SHOULD* have an extension
        extension = SubmissionExerciseDeviation(exercise=self.SE1, user=self.s1,
                                                new_deadline=datetime.datetime(2050, 1, 1, tzinfo=pytz.UTC))
        extension.save()

        res = self.get(self.SE1, self.s1)
        self.assertContains(res, "This exercise was closed on")
        self.assertContains(res, "However, you have an extended deadline until")
        self.assertEqual(res.context_data['disable_form'], False)

        # student *SHOULD NOT* have an extension
        extension.new_deadline = "2006-01-01 10:10+03:00"
        extension.save()

        res = self.get(self.SE1, self.s1)
        self.assertContains(res, "This exercise was closed on")
        self.assertNotContains(res, "However, you have an extended deadline until")
        self.assertEqual(res.context_data['disable_form'], True)

    def test_student_can_submit(self):

        res = self.post(self.SE1, self.s1, {'text': 'bla'})
        self.assertEqual(res.status_code, 302)  # redirect to submission view

    def test_studentCannotSubmitMultipleTimes(self):

        # student cannot submit multiple times SubmissionExercises
        for s in [self.s1, self.s2]:

            self.create_originalsubmission_for(self.SE1, s)

            res = self.get(self.SE1, s)
            self.assertContains(res, "You have reached the maximum number of submissions")
            self.assertEqual(res.context_data['disable_form'], True)

            # this will try to post (the form is disabled but the user could use devtools) -> should not succeed
            res = self.post(self.SE1, s, {'text': 'bla'})
            self.assertContains(res, "You cannot submit")
            self.assertEqual(res.context_data['disable_form'], True)

        self.assertEqual(OriginalSubmission.objects.count(), 2)

        # this will create two reviewlocks since both loaded the page
        for s in [self.s1, self.s2]:
            res = self.get(self.RE1, s)
            self.assertContains(res, f"text by {self.s1 if s == self.s2 else self.s2}")

        self.assertEqual(ReviewLock.objects.all().count(), 2)

        # after submissions are created, no more reviews can be made
        for s in [self.s1, self.s2]:

            rsub = ReviewSubmission(course=self.course,
                                    exercise=self.RE1,
                                    submitter_user=s,
                                    reviewed_submission=ReviewLock.objects.get(user=s).original_submission)
            rsub.save_and_destroy_lock()
            res = self.get(self.RE1, s)
            self.assertContains(res, 'You have already submitted your peer-reviews to this exercise.')

    def test_reviewlocks_created_correctly(self):

        se = SubmissionExercise.objects.get(pk=1)
        for s in self.students:
            OriginalSubmission(course=self.course,
                               submitter_user=s,
                               exercise=se,
                               text=f"text by {s}").save()

        # this will create two reviewlocks since both loaded the page
        re = ReviewExercise.objects.get(reviewable_exercise=se)
        for s in [self.s1, self.s2]:
            request = self.factory.get('/courses/prog1/F2018/exercises/r/1/')
            request.user = s
            self.kwargs['pk'] = re.pk

            response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
            self.assertContains(response, f"text by {self.s1 if s == self.s2 else self.s2}")

        self.assertEqual(ReviewLock.objects.all().count(), 2)

        # the same reviewlocks are still used since no reviews have been made
        for s in [self.s1, self.s2]:
            request = self.factory.get('/courses/prog1/F2018/exercises/r/1/')
            request.user = s
            self.kwargs['pk'] = re.pk

            response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
            self.assertContains(response, f"text by {self.s1 if s == self.s2 else self.s2}")

        self.assertEqual(ReviewLock.objects.all().count(), 2)

        # after submissions are created, no more reviews can be made
        for s in [self.s1, self.s2]:
            rlock = ReviewLock.objects.get(user=s)

            rsub = ReviewSubmission(course=self.course,
                                    exercise=re,
                                    submitter_user=s,
                                    reviewed_submission=rlock.original_submission)
            rsub.save_and_destroy_lock()

            request = self.factory.get('/courses/prog1/F2018/exercises/r/1/')
            request.user = s
            self.kwargs['pk'] = re.pk
            response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
            self.assertContains(response, 'You have already submitted your peer-reviews to this exercise.')

        self.assertEqual(ReviewLock.objects.all().count(), 0)
        # now in the system: 4 OS, 0 RL, 2 RS

        # s4 loads the page -> RL should be for s3
        request = self.factory.get('/courses/prog1/F2018/exercises/r/1/')
        request.user = self.s4
        self.kwargs['pk'] = re.pk
        response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, f"text by {self.s3}")
        self.assertEqual(ReviewLock.objects.all().count(), 1)

        re.max_submission_count = 2
        re.save()

        # s1 loads the page -> RL should be for s4 since no RLs for s4 exist yet
        request.user = self.s1
        response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, f"text by {self.s4}")
        self.assertEqual(ReviewLock.objects.all().count(), 2)

        # s2 loads the page -> nothing to review since all can recieve only one
        request.user = self.s2
        response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, f"no-submissions-for-peer-review")
        self.assertEqual(ReviewLock.objects.all().count(), 2)

        # increase the number of reviews an OS can get
        re.max_reviews_per_submission = 2
        re.save()

        # s2 should now get s3 since cannot get himself and s1 already done
        request.user = self.s2
        self.kwargs['pk'] = re.pk
        response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, f"text by {self.s3}")
        self.assertEqual(ReviewLock.objects.all().count(), 3)

        # s3 has not yet loaded the page -> should get s1
        request.user = self.s3
        self.kwargs['pk'] = re.pk
        response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, f"text by {self.s1}")
        self.assertEqual(ReviewLock.objects.all().count(), 4)

    def test_reviewlocks_created_correctly_for_groups(self):

        groups = [
            StudentGroup.objects.create(course=self.course,
                                        name="g1",
                                        student_usernames=[self.s1.email, self.s2.email]),
            StudentGroup.objects.create(course=self.course,
                                        name="g2",
                                        student_usernames=[self.s3.email, self.s4.email]),
            StudentGroup.objects.create(course=self.course,
                                        name="g3",
                                        student_usernames=[self.s5.email, self.s6.email]),
        ]

        se = SubmissionExercise.objects.get(name='T1 TEXT')
        se.use_groups = True
        se.save()

        # OS for all groups
        for s, g in [(self.s1, groups[0]), (self.s3, groups[1]), (self.s5, groups[2])]:
            self.post(se, s, {'text': f'text by {g.name}'})
        self.assertEqual(OriginalSubmission.objects.count(), 3)

        re = se.review_exercise
        re.use_groups = True
        re.save()

        # g1 -> g2, g2 -> g1
        request = self.factory.get('/courses/prog1/F2018/exercises/r/1/')
        self.kwargs['pk'] = re.pk
        for s, target_name in [(self.s1, 'g2'), (self.s2, 'g2'), (self.s3, 'g1'), (self.s4, 'g1')]:
            request.user = s
            response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
            self.assertContains(response, f"text by {target_name}")

        self.assertEqual(ReviewLock.objects.all().count(), 2)

        # g1 -> review for g2
        rlock = re.reviewlocks_for(self.s1).first()
        rsub = ReviewSubmission(course=self.course,
                                exercise=re,
                                submitter_user=self.s1,
                                submitter_group=groups[0],
                                reviewed_submission=rlock.original_submission)
        rsub.save_and_destroy_lock()

        for s in [self.s1, self.s2]:
            request.user = s
            response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
            self.assertContains(response, 'You have already submitted your peer-reviews')
            self.assertEqual(response.context_data['disable_form'], True)

        self.assertEqual(ReviewLock.objects.all().count(), 1)

        # increase sub count that groups can do. g1 -> g3
        re.max_submission_count = 2
        re.save()

        for s, target_name in [(self.s1, 'g3'), (self.s2, 'g3')]:
            request.user = s
            response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
            self.assertContains(response, f"text by {target_name}")
        self.assertEqual(ReviewLock.objects.all().count(), 2)

        # nothing left for g3 to review
        for s in [self.s5, self.s6]:
            request.user = s
            response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
            self.assertContains(response, 'no-submissions-for-peer-review')
            self.assertEqual(response.context_data['disable_form'], True)
        self.assertEqual(ReviewLock.objects.all().count(), 2)

        # increase how many reviews can receive. g3 -> g1 since g1 oldest and 1 review
        re.max_reviews_per_submission = 2
        re.save()

        for s, target_name in [(self.s5, 'g1'), (self.s6, 'g1')]:
            request.user = s
            response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
            self.assertContains(response, f"text by {target_name}")
        self.assertEqual(ReviewLock.objects.all().count(), 3)

    def test_expiry_hours(self):

        # create original submissions for all 4 students
        se = SubmissionExercise.objects.get(pk=1)
        for s in self.students:
            OriginalSubmission(course=self.course,
                               submitter_user=s,
                               exercise=se,
                               text=f"text by {s}").save()

        re = ReviewExercise.objects.get(reviewable_exercise=se)

        # create two locks, for s2 and s3, by loading the page
        for s in [self.s2, self.s3]:
            request = self.factory.get('/courses/prog1/F2018/exercises/r/1/')
            request.user = s
            self.kwargs['pk'] = re.pk

            response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
            self.assertContains(response, f"text by {self.s1 if s == self.s2 else self.s2}")

        self.assertEqual(ReviewLock.objects.all().count(), 2)

        # make exercise expire locks in 10 hours
        re.reviewlock_expiry_hours = 10
        re.save()

        # move locks 5 hours back in time
        # these locks should NOT expire just yet
        ReviewLock.objects.all().update(created=timezone.now()-timezone.timedelta(hours=5))

        # load the page -> nothing should just yet expire, third lock should appear
        request = self.factory.get('/courses/prog1/F2018/exercises/r/1/')
        request.user = self.s4
        self.kwargs['pk'] = re.pk
        response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)

        self.assertEqual(ReviewLock.objects.all().count(), 3)

        # test that created time of a ReviewLock is refreshed on access
        rl_s4 = ReviewLock.objects.get(user=self.s4)
        created_before_refresh = rl_s4.created
        ReviewExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertEqual(ReviewLock.objects.all().count(), 3)
        rl_s4.refresh_from_db()
        self.assertNotEqual(created_before_refresh, rl_s4.created)

        # change expiry to 1 hour -> all locks should be expirying now
        re.reviewlock_expiry_hours = 1
        re.save()

        request.user = self.s1
        # this should create a lock for s1 and expire locks of s2 and s3
        response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)

        self.assertEqual(ReviewLock.objects.all().count(), 2)
        self.assertEqual(ReviewLock.objects.filter(user=self.s1).exists(), True)
        self.assertEqual(ReviewLock.objects.filter(user=self.s4).exists(), True)

        # make s1 rl expire -> still post the form
        # this simulates how someone may have the browser open for a long time

        rl_s1 = ReviewLock.objects.get(user=self.s1)
        rl_s1.created = rl_s1.created.replace(hour=rl_s1.created.hour-5)
        rl_s1.save()
        rl_s1_reviewable_pk = rl_s1.original_submission.pk
        # this will expire rl for s1
        request.user = self.s3
        ReviewExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertEqual(ReviewLock.objects.filter(user=self.s1).exists(), False)

        # there should be locks for s3 and s4
        self.assertEqual(ReviewLock.objects.all().count(), 2)
        self.assertEqual(re.submissions.filter(submitter_user=self.s1).exists(), False)

        answers = {
            'choice': [rl_s1_reviewable_pk],
            'Q-PREFIX-2--question': ['2'],
            'Q-PREFIX-2--value_choice': ['1'],
            'Q-PREFIX-1--question': ['1'],
            'Q-PREFIX-1--value_text': ['some text']
        }
        self.post(re, self.s1, answers)
        self.assertEqual(re.submissions.filter(submitter_user=self.s1).exists(), True)

    def test_teacherCanSubmitMultipleTimes(self):

        exercise = SubmissionExercise.objects.get(pk=1)
        OriginalSubmission(course=self.course, submitter_user=self.t1, exercise=exercise, text="jadajada").save()
        OriginalSubmission(course=self.course, submitter_user=self.t1, exercise=exercise, text="jadajada").save()
        OriginalSubmission(course=self.course, submitter_user=self.t1, exercise=exercise, text="jadajada").save()

        request = self.factory.get('/courses/prog1/F2018/exercises/s/1/')
        request.user = self.t1
        self.kwargs['pk'] = 1

        response = SubmissionExerciseDetailView.as_view()(request, **self.kwargs)

        self.assertNotContains(response, "You have reached the maximum number of submissions")
        self.assertContains(response, "Submit")

    def test_submissionStatesWork(self):

        se = SubmissionExercise.objects.get(name='T5 STATE')

        subs = []
        for s in self.students[:2]:
            response = self.post(se, s, {'text': f'answer by {s.username}'})
            sub = OriginalSubmission.objects.get(pk=resolve(response.url).kwargs['sub_pk'])
            self.assertEqual(sub.state, OriginalSubmission.SUBMITTED)
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
        self.assertContains(response, "no-submissions-for-peer-review")

        subs[0].state = OriginalSubmission.READY_FOR_REVIEW
        subs[0].save()

        r_exer = ReviewExercise.objects.get(name='T5 STATE REVIEW')
        request = self.factory.get(r_exer.get_absolute_url())
        request.user = self.s1
        self.kwargs['pk'] = r_exer.pk
        response = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "answer by student2")
        self.assertEqual(ReviewLock.objects.count(), 1)

    def test_reviewexercise_type_choose(self):

        se = SubmissionExercise.objects.get(name="T1 TEXT")
        re = ReviewExercise.objects.get(name="T1 TEXT REVIEW")

        re.type = ReviewExercise.CHOOSE
        re.require_original_submission = False
        re.save()

        res = self.get(re, self.s1)
        self.assertEqual(len(res.context_data['chooseform_options_list']), 0)

        subs = self.create_originalsubmission_for(se, [self.s1, self.s2, self.s3])

        res = self.get(re, self.s1)
        self.assertEqual(len(res.context_data['chooseform_options_list']), 2)

        re.can_review_own_submission = True
        re.save()

        res = self.get(re, self.s1)
        self.assertEqual(len(res.context_data['chooseform_options_list']), 3)

        re.require_original_submission = True
        re.save()

        res = self.get(re, self.s4)
        self.assertEqual('chooseform_options_list' in res.context_data, False)
        answers = {
            'choice': [subs[0].pk],
            'Q-PREFIX-2--question': ['2'],
            'Q-PREFIX-2--value_choice': ['1'],
            'Q-PREFIX-1--question': ['1'],
            'Q-PREFIX-1--value_text': ['some text']
        }
        res = self.post(re, self.s4, answers)
        self.assertEqual('You cannot submit' in res.rendered_content, True)
        self.assertEqual(ReviewSubmission.objects.count(), 0)

        re.require_original_submission = False
        re.save()

        res = self.post(re, self.s4, answers)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(ReviewSubmission.objects.count(), 1)

        ReviewSubmission.objects.all().delete()
        answers['choice'] = [666]
        self.assertRaises(PermissionDenied, self.post, re, self.s4, answers)
        self.assertEqual(ReviewSubmission.objects.count(), 0)

    def test_reviewexercise_type_group(self):

        se = SubmissionExercise.objects.get(name="T1 TEXT")
        re = ReviewExercise.objects.get(name="T1 TEXT REVIEW")

        se.type = SubmissionExercise.GROUP_NO_SUBMISSION
        se.save()

        re.type = ReviewExercise.GROUP
        re.use_groups = True
        re.save()

        temp_email = "temp-test@temp-test.com"
        g = StudentGroup(course=se.course,
                         name="g1",
                         student_usernames=[self.s1.email, self.s2.email, temp_email]
                         )
        g.save()

        user_count_before = User.objects.count()
        self.assertEqual(0, se.submissions.count())

        request = self.factory.get(re.get_absolute_url())
        request.user = self.s1
        self.kwargs['pk'] = re.pk

        # should create temp user for temp-test@temp-test.com
        # should have three orig subs because three group members
        res = ReviewExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertEqual(user_count_before + 1, User.objects.count())
        self.assertEqual(3, se.submissions.count())
        # when students review each other, inlined options are not shown, only ChooseForm dropdown
        self.assertEqual(len(res.context_data['chooseform_options_list']), 0)

        temp_user = User.objects.get(email=temp_email)
        self.assertEqual(temp_user.temporary, True)
        self.assertEqual(temp_user.lti, False)

        request.user = self.s2
        ReviewExerciseDetailView.as_view()(request, **self.kwargs)

        # page load as another user of the group shouldn't have any effect
        self.assertEqual(user_count_before + 1, User.objects.count())
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

        # create actual user. this will be used to simulate sihbboleth login in a future time
        # when the system allready has a submission temporarily made for this user.
        actual_user = User.objects.create(username="actual_user",
                                          email=temp_email)
        actual_user.set_password("actual_password")
        actual_user.save()

        self.assertEqual(2, User.objects.filter(email=temp_email).count())

        orig_submitter = OriginalSubmission.objects.get(submitter_user__email=temp_email).submitter_user.username

        # logging in a user would normally trigger users/receivers.py which will:
        #   - find all submissions done with a temp user using same email
        #   - transfer all submissions to this actual user
        #   - delete temp user
        # here we'll just call the signal handler directly

        fake_request = HttpRequest()
        fake_request.LTI_MODE = False
        fake_request.user = actual_user
        change_original_submission_submitters(None, request=fake_request, user=actual_user)

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

    def test_nothing_was_found_for_peer_review(self):
        # check that helper text no submissions was found to be peer-reviewed
        # is shown to the user correctly. if RE.type is RANDOM, then the text is
        # in an alert-div. if RE.type is CHOOSE, then the text is in form helper.
        # the error msg should be displayed exactly once (thus count=1 below).

        # no personal submission yet
        self.assertNotContains(self.get(self.RE1, self.s1), 'no-submissions-for-peer-review')
        self.create_originalsubmission_for(self.SE1, self.s1)
        self.assertContains(self.get(self.RE1, self.s1), 'no-submissions-for-peer-review', count=1)
        # now there's something that can be reviewed
        self.create_originalsubmission_for(self.SE1, self.s2)
        self.assertNotContains(self.get(self.RE1, self.s1), 'no-submissions-for-peer-review')

        OriginalSubmission.objects.all().delete()
        self.RE1.type = ReviewExercise.CHOOSE
        self.RE1.save()

        # no personal submission yet
        self.assertNotContains(self.get(self.RE1, self.s1), 'no-submissions-for-peer-review')
        self.create_originalsubmission_for(self.SE1, self.s1)
        self.assertContains(self.get(self.RE1, self.s1), 'no-submissions-for-peer-review', count=1)
