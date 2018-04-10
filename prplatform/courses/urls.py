from django.conf.urls import url

from . import views

app_name = "courses"
urlpatterns = [
    url(regex=r"^$", view=views.CourseListView.as_view(), name="list"),
]
