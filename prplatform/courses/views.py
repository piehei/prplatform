from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import ProcessFormView
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import BaseCourse, Course
from .mixins import CourseMixin

from prplatform.users.models import User


# def is_teacher_decorator():
#     def decorator(func):
#         def wrapper(request, *args, **kwargs):
#             # nananannanana
#             return func(request, *args, **kwargs)
#         return wrapper
#     return decorator

class CourseMixin:

    def get_object(self):
        base_course = get_object_or_404(BaseCourse, url_slug=self.kwargs['base_url_slug'])
        course = get_object_or_404(Course, base_course=base_course, url_slug=self.kwargs['url_slug'])
        return course


class CourseDetailView(CourseMixin, DetailView):
    model = Course
    slug_field = "url_slug"
    slug_url_kwarg = "url_slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['teacher'] = context['course'].base_course.is_teacher(self.request.user)
        context['enrolled'] = context['course'].is_enrolled(self.request.user)
        return context


class CourseUpdateView(CourseMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Course
    fields = ['start_date', 'end_date']
    # 403 if not teacher
    raise_exception = True

    def test_func(self):
        return self.get_object().base_course.is_teacher(self.request.user)


class CourseListView(ListView):
    model = Course


class CourseEnroll(CourseMixin, ProcessFormView):
    model = Course

    def get_success_url(self):
        return reverse("courses:detail", kwargs={'url_slug': self.kwargs['url_slug'],
                       'base_url_slug': self.kwargs['base_url_slug']})

    def post(self, request, *args, **kwargs):
        course = self.get_object()
        if not course.is_enrolled(self.request.user):
            course.enroll(self.request.user)
            return HttpResponseRedirect(reverse("courses:detail", kwargs={'url_slug': self.kwargs['url_slug'],
                                    'base_url_slug': self.kwargs['base_url_slug']}))
