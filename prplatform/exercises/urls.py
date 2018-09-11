from django.urls import path
from django.conf.urls import url, include

from . import views
from .question_views import QuestionDetailView

app_name = "exercises"

urlpatterns = [
    path('s/<int:pk>/', view=views.SubmissionExerciseDetailView.as_view(), name="submission-detail"),
    path('r/<int:pk>/', view=views.ReviewExerciseDetailView.as_view(), name="review-detail"),
    path('q/<int:pk>/', view=QuestionDetailView.as_view(), name="question-detail"),
    path('s/<int:pk>/submissions/', include('prplatform.submissions.urls', namespace="submissions"))
]
