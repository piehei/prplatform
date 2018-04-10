from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView

from .models import Course


class CourseDetailView(DetailView):
    model = Course
    # slug_field = "name"
    # lug_url_kwarg = "name"


class CourseCreateView(CreateView):
    model = Course
    fields = ['name']

    # def get_success_url(self):
        # return reverse("courses:detail", kwargs={"name": self.request.course.name})


class CourseListView(ListView):
    model = Course
