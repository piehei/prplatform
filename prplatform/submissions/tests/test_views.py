from django.test import RequestFactory, TestCase
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied

from prplatform.users.models import User
from prplatform.courses.models import Course
from prplatform.exercises.models import SubmissionExercise, ReviewExercise
from prplatform.exercises.question_models import Question

from prplatform.submissions.models import OriginalSubmission, ReviewSubmission, Answer
from prplatform.submissions.views import OriginalSubmissionListView, DownloadSubmissionView, ReviewSubmissionListView, ReviewSubmissionDetailView


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
        self.assertEqual(response.context_data['originalsubmission_list'].count(), 1)
        self.assertNotContains(response, "student2")  # hacky
        self.assertNotContains(response, "student3")

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
        self.assertEqual(response.context_data['originalsubmission_list'].count(), 4)
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
        self.assertEqual(response.context_data['reviewsubmission_list'].count(), 2)
        self.assertContains(response, "student1")  # hacky
        self.assertContains(response, "student2")

        # student1 sees reviews of him by student2
        request = self.factory.get('/courses/prog1/F2018/submissions/r/1/list/?mode=my')
        request.user = users[0]
        self.kwargs['pk'] = 1
        response = ReviewSubmissionListView.as_view()(request, **self.kwargs)
        self.assertEqual(ReviewSubmission.objects.all().count(), 2)
        self.assertEqual(response.context_data['reviewsubmission_list'].count(), 1)
        self.assertEqual(response.context_data['reviewsubmission_list'][0].submitter_user, users[1])

        # student2 sees reviews of him by student1
        request = self.factory.get('/courses/prog1/F2018/submissions/r/1/list/?mode=my')
        request.user = users[1]
        self.kwargs['pk'] = 1
        response = ReviewSubmissionListView.as_view()(request, **self.kwargs)
        self.assertEqual(ReviewSubmission.objects.all().count(), 2)
        self.assertEqual(response.context_data['reviewsubmission_list'].count(), 1)
        self.assertEqual(response.context_data['reviewsubmission_list'][0].submitter_user, users[0])

    def test_ReviewSubPagePermissionsWork(self):

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
            reviewed_sub = OriginalSubmission.objects.filter(exercise=sub_exercise) \
                                                            .exclude(submitter_user=user).first()
            rs = ReviewSubmission.objects.create(course=course, submitter_user=user,
                                                 exercise=rev_exercise, reviewed_submission=reviewed_sub)
            Answer.objects.create(submission=rs, value_text="juupase juu", question=Question.objects.get(pk=1))
            Answer.objects.create(submission=rs, value_choice="1", question=Question.objects.get(pk=2))


        # teacher sees all reviews
        request = self.factory.get('/courses/prog1/F2018/submissions/r/1/1/')
        request.user = User.objects.get(username="teacher1")
        self.kwargs['pk'] = 1
        self.kwargs['sub_pk'] = 1
        response = ReviewSubmissionDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "juupase juu")
        self.assertContains(response, "Score the work")

        # student sees hidden answer *given* by him
        request = self.factory.get('/courses/prog1/F2018/submissions/r/1/1/')
        request.user = users[0]
        self.kwargs['pk'] = 1
        self.kwargs['sub_pk'] = 1
        response = ReviewSubmissionDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "juupase juu")
        self.assertContains(response, "Score the work")

        # student cannot see answer to a hidden question
        request = self.factory.get('/courses/prog1/F2018/submissions/r/1/1/')
        request.user = users[1]
        self.kwargs['pk'] = 1
        self.kwargs['sub_pk'] = 1
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
