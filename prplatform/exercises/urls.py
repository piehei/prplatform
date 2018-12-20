from django.urls import path

from . import views
from .deviation_views import (
        DeviationCreateView,
        DeviationDeleteView,
        DeviationListView,
    )
from .question_views import (
        QuestionCreateView,
        QuestionDetailView,
        QuestionListView,
        QuestionUpdateView,
    )


app_name = "exercises"

urlpatterns = [

    # SUBMISSION EXERCISES
    path('s/<int:pk>/', view=views.SubmissionExerciseDetailView.as_view(), name="submission-detail"),
    path('s/<int:pk>/as_student/', view=views.SubmissionExerciseAsStudent.as_view(), name="submission-as-student"),

    path('s/<int:pk>/deviations',
         DeviationListView.as_view(), {'deviation_type': 's'}, name="submission-deviation-list"),
    path('s/<int:pk>/deviations/create',
         DeviationCreateView.as_view(), {'deviation_type': 's'}, name="submission-deviation-create"),
    path('s/<int:exer_pk>/deviations/<int:pk>/delete',
         DeviationDeleteView.as_view(), {'deviation_type': 's'}, name="submission-deviation-delete"),

    # REVIEW EXERCISES
    path('r/<int:pk>/', view=views.ReviewExerciseDetailView.as_view(), name="review-detail"),
    path('r/<int:pk>/as_student/', view=views.ReviewExerciseAsStudent.as_view(), name="review-as-student"),

    path('r/<int:pk>/deviations',
         DeviationListView.as_view(), {'deviation_type': 'r'}, name="review-deviation-list"),
    path('r/<int:pk>/deviations/create',
         DeviationCreateView.as_view(), {'deviation_type': 'r'}, name="review-deviation-create"),
    path('r/<int:exer_pk>/deviations/<int:pk>/delete',
         DeviationDeleteView.as_view(), {'deviation_type': 'r'}, name="review-deviation-delete"),


    # REVIEW QUESTIONS
    path('r/<int:pk>/q', view=QuestionListView.as_view(), name="question-list"),
    path('r/<int:rpk>/q/create/', view=QuestionCreateView.as_view(), name="question-create"),
    path('r/<int:rpk>/q/<int:pk>/', view=QuestionDetailView.as_view(), name="question-detail"),
    path('r/<int:rpk>/q/<int:pk>/update', view=QuestionUpdateView.as_view(), name="question-update"),
]
