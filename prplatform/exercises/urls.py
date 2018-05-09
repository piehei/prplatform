from django.urls import path
from django.conf.urls import url

from . import views

app_name = "exercises"
urlpatterns = [
    # path('', view=views.ExerciseListView.as_view(), name="exercise-list"),
    path('s/<int:pk>/', view=views.SubmissionExerciseDetailView.as_view(), name="submission-detail"),
    path('r/<int:pk>/', view=views.ReviewExerciseDetailView.as_view(), name="review-detail"),
]
