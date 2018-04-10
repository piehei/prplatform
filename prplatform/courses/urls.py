from django.conf.urls import url

from . import views

app_name = "courses"
urlpatterns = [
    url(regex=r"^$", view=views.CourseListView.as_view(), name="list"),
    url(regex=r"create/$", view=views.CourseCreateView.as_view(), name="create"),
]
