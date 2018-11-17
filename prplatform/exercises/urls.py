from django.urls import path
from django.conf.urls import url, include

from . import views
from .question_views import QuestionCreateView, QuestionUpdateView, QuestionDetailView, QuestionListView
from .deviation_views import SEDeviationListView, SEDeviationCreateView, SEDeviationDeleteView


app_name = "exercises"

urlpatterns = [
    path('s/<int:pk>/', view=views.SubmissionExerciseDetailView.as_view(), name="submission-detail"),
    path('s/<int:pk>/deviations', view=SEDeviationListView.as_view(), name="submission-deviation-list"),
    path('s/<int:pk>/deviations/create', view=SEDeviationCreateView.as_view(), name="submission-deviation-create"),
    path('s/<int:rpk>/deviations/<int:pk>/delete', view=SEDeviationDeleteView.as_view(), name="submission-deviation-delete"),
    path('r/<int:pk>/', view=views.ReviewExerciseDetailView.as_view(), name="review-detail"),
    path('r/<int:pk>/q', view=QuestionListView.as_view(), name="question-list"),
    path('r/<int:rpk>/q/create/', view=QuestionCreateView.as_view(), name="question-create"),
    path('r/<int:rpk>/q/<int:pk>/', view=QuestionDetailView.as_view(), name="question-detail"),
    path('r/<int:rpk>/q/<int:pk>/update', view=QuestionUpdateView.as_view(), name="question-update"),
    path('s/<int:pk>/submissions/', include('prplatform.submissions.urls', namespace="submissions"))
]
