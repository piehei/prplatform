from django.urls import path
from django.conf.urls import include, url

from . import views
from prplatform.exercises.views import SubmissionExerciseCreateView, SubmissionExerciseUpdateView, ReviewExerciseCreateView, ReviewExerciseUpdateView, SubmissionExerciseDeleteView, ReviewExerciseDeleteView
from prplatform.submissions.views import OriginalSubmissionUpdateView
from prplatform.exercises.question_views import QuestionCreateView, QuestionUpdateView
app_name = "courses"
urlpatterns = [
    url(regex=r"^$", view=views.CourseListView.as_view(), name="list"),
    path('<slug:base_url_slug>/<slug:url_slug>/', view=views.CourseDetailView.as_view(), name="detail"),
    path('<slug:base_url_slug>/<slug:url_slug>/enroll', view=views.CourseEnroll.as_view(), name="enroll"),
    path('<slug:base_url_slug>/<slug:url_slug>/exercises/', include('prplatform.exercises.urls', namespace="exercises")),
    path('<slug:base_url_slug>/<slug:url_slug>/submissions/', include('prplatform.submissions.urls', namespace="submissions")),
    path('<slug:base_url_slug>/<slug:url_slug>/teacher', view=views.CourseTeacherView.as_view(), name="teacher"),
    path('<slug:base_url_slug>/<slug:url_slug>/teacher/groups', view=views.CourseGroupView.as_view(), name="groups"),
    path('<slug:base_url_slug>/<slug:url_slug>/teacher/update', view=views.CourseUpdateView.as_view(), name="update"),
    path('<slug:base_url_slug>/<slug:url_slug>/teacher/create/submission', view=SubmissionExerciseCreateView.as_view(), name="create-submission-exercise"),
    path('<slug:base_url_slug>/<slug:url_slug>/teacher/create/review', view=ReviewExerciseCreateView.as_view(), name="create-review-exercise"),
    path('<slug:base_url_slug>/<slug:url_slug>/teacher/create/question', view=QuestionCreateView.as_view(), name="create-question"),
    path('<slug:base_url_slug>/<slug:url_slug>/teacher/update/question/<int:pk>', view=QuestionUpdateView.as_view(), name="update-question"),
    path('<slug:base_url_slug>/<slug:url_slug>/teacher/update/s/<int:pk>', view=SubmissionExerciseUpdateView.as_view(), name="update-submission-exercise"),
    path('<slug:base_url_slug>/<slug:url_slug>/teacher/update/r/<int:pk>', view=ReviewExerciseUpdateView.as_view(), name="update-review-exercise"),
    path('<slug:base_url_slug>/<slug:url_slug>/teacher/delete/s/<int:pk>', view=SubmissionExerciseDeleteView.as_view(), name="delete-submission-exercise"),
    path('<slug:base_url_slug>/<slug:url_slug>/teacher/delete/r/<int:pk>', view=ReviewExerciseDeleteView.as_view(), name="delete-review-exercise"),
    path('<slug:base_url_slug>/<slug:url_slug>/teacher/update-state/s/<int:pk>', view=OriginalSubmissionUpdateView.as_view(), name="update-submission-state"),
]
