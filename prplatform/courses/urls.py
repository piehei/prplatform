from django.urls import path
from django.conf.urls import include, url

from . import views
from prplatform.exercises.views import ExerciseCreateView, GeneralExerciseUpdateView

app_name = "courses"
urlpatterns = [
    url(regex=r"^$", view=views.CourseListView.as_view(), name="list"),
    path('<slug:base_url_slug>/<slug:url_slug>/', view=views.CourseDetailView.as_view(), name="detail"),
    path('<slug:base_url_slug>/<slug:url_slug>/enroll', view=views.CourseEnroll.as_view(), name="enroll"),
    path('<slug:base_url_slug>/<slug:url_slug>/exercises/', include('prplatform.exercises.urls', namespace="exercises")),
    path('<slug:base_url_slug>/<slug:url_slug>/teacher', view=views.CourseTeacherView.as_view(), name="teacher"),
    path('<slug:base_url_slug>/<slug:url_slug>/teacher/update', view=views.CourseUpdateView.as_view(), name="update"),
    path('<slug:base_url_slug>/<slug:url_slug>/teacher/create', view=ExerciseCreateView.as_view(), name="create-exercise"),
    path('<slug:base_url_slug>/<slug:url_slug>/teacher/<int:pk>/update', view=GeneralExerciseUpdateView.as_view(), name="update-exercise"),
]
