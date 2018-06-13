from django.urls import path
from django.conf.urls import url

from . import views

app_name = "submissions"
urlpatterns = [
        path('s/<int:pk>/list/', view=views.OriginalSubmissionListView.as_view(), name="original-list"),
        path('r/<int:pk>/list/', view=views.ReviewSubmissionListView.as_view(), name="review-list"),
        path('s/<int:pk>/<int:sub_pk>/', view=views.OriginalSubmissionDetailView.as_view(), name="original-detail"),
        path('r/<int:pk>/<int:sub_pk>/', view=views.ReviewSubmissionDetailView.as_view(), name="review-detail"),
]
