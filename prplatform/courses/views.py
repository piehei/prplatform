from django.urls import reverse
from django.views.generic import ListView, CreateView

from .models import Course


class CourseCreateView(CreateView):
    model = Course
    fields = ['name']

    def get_success_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})


class CourseListView(ListView):
    model = Course
