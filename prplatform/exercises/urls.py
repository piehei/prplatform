from django.urls import path
from django.conf.urls import url, include

from . import views
from .question_views import QuestionCreateView, QuestionUpdateView, QuestionDetailView, QuestionListView

app_name = "exercises"

urlpatterns = [
    path('s/<int:pk>/', view=views.SubmissionExerciseDetailView.as_view(), name="submission-detail"),
    path('r/<int:pk>/', view=views.ReviewExerciseDetailView.as_view(), name="review-detail"),
    path('r/<int:pk>/q', view=QuestionListView.as_view(), name="question-list"),
    path('r/<int:pk>/q/create/', view=QuestionCreateView.as_view(), name="question-create"),
    path('r/<int:rpk>/q/<int:pk>/', view=QuestionDetailView.as_view(), name="question-detail"),
    path('r/<int:rpk>/q/<int:pk>/update', view=QuestionUpdateView.as_view(), name="question-update"),
    path('s/<int:pk>/submissions/', include('prplatform.submissions.urls', namespace="submissions"))
]
