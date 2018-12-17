from django.urls import path

from . import views

app_name = "submissions"
urlpatterns = [
        path('s/<int:pk>/list/', view=views.OriginalSubmissionListView.as_view(), name="original-list"),
        path('r/<int:pk>/list/', view=views.ReviewSubmissionListView.as_view(), name="review-list"),
        path('r/<int:pk>/embedded_list/', view=views.ReviewSubmissionEmbeddedFeedbackList.as_view(), name="review-list-embedded"),
        path('s/<int:pk>/<int:sub_pk>/', view=views.OriginalSubmissionDetailView.as_view(), name="original-detail"),
        path('s/<int:pk>/<int:sub_pk>/delete', view=views.OriginalSubmissionDeleteView.as_view(), name="original-delete"),
        path('r/<int:pk>/<int:sub_pk>/', view=views.ReviewSubmissionDetailView.as_view(), name="review-detail"),
        path('r/<int:pk>/<int:sub_pk>/delete', view=views.ReviewSubmissionDeleteView.as_view(), name="review-delete"),
        path('download/<int:pk>/', view=views.DownloadSubmissionView.as_view(), name="download")
]
