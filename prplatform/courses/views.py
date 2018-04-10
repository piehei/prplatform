from django.views.generic import ListView

from .models import Course


class CourseListView(ListView):
    model = Course
