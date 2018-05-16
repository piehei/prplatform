from django.urls import path
from django.conf.urls import url

from . import views

app_name = "submissions"
urlpatterns = [
    path('', view=views.SubmissionListView.as_view(), name="submission-list"),
    path('<int:sub_pk>/', view=views.SubmissionDetailView.as_view(), name="submission-detail"),
]
