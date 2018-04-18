from django.urls import path
from django.conf.urls import url

from . import views

app_name = "courses"
urlpatterns = [
    url(regex=r"^$", view=views.CourseListView.as_view(), name="list"),
    path('<slug:base_url_slug>/<slug:url_slug>/', view=views.CourseDetailView.as_view(), name="detail"),
    path('<slug:base_url_slug>/<slug:url_slug>/update', view=views.CourseUpdateView.as_view(), name="update"),
    path('<slug:base_url_slug>/<slug:url_slug>/enroll', view=views.CourseEnroll.as_view(), name="enroll"),
    path('<slug:base_url_slug>/<slug:url_slug>/<int:pk>', view=views.CourseEnroll.as_view(), name="enroll")

]
