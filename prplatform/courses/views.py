from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import ProcessFormView
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages

from .models import BaseCourse, Course

# def is_teacher_decorator():
#     def decorator(func):
#         def wrapper(request, *args, **kwargs):
#             # nananannanana
#             return func(request, *args, **kwargs)
#         return wrapper
#     return decorator


class CourseContextMixin:

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, url_slug=self.kwargs['url_slug'],
                                              base_course__url_slug=self.kwargs['base_url_slug'])
        context['teacher'] = context['course'].is_teacher(self.request.user)
        return context


class IsTeacherMixin(UserPassesTestMixin, LoginRequiredMixin):
    """ This makes sure that the user is logged in and is a teacher
        of the course. 403 forbidden is raised if not. """

    raise_exception = True
    permission_denied_message = "Only teacher of the course can access this page."

    def test_func(self):
        bc = get_object_or_404(BaseCourse, url_slug=self.kwargs['base_url_slug'])
        return bc.is_teacher(self.request.user)


class IsSubmitterMixin(UserPassesTestMixin, LoginRequiredMixin):

    raise_exception = True
    permission_denied_message = "Only the submitter can access this page."

    def test_func(self):
        return self.get_object().submitter == self.request.user


class IsEnrolledMixin(UserPassesTestMixin, LoginRequiredMixin):

    raise_exception = True
    permission_denied_message = "Only enrolled users can access this page."

    def test_func(self):
        print("moi")
        enrolled = self.get_object().course.is_enrolled(self.request.user)
        teacher = self.get_object().course.is_teacher(self.request.user)
        return enrolled or teacher


class IsSubmitterOrTeacherMixin(UserPassesTestMixin, LoginRequiredMixin):

    raise_exception = True
    permission_denied_message = "Only the submitter or a teacher can access this page."

    def test_func(self):
        is_submitter = self.get_object().submitter == self.request.user
        is_teacher = get_object_or_404(BaseCourse, url_slug=self.kwargs['base_url_slug']).is_teacher(self.request.user)
        return is_submitter or is_teacher


class CourseMixin:
    """ This returns the course object itself """

    def get_object(self):
        return get_object_or_404(Course, url_slug=self.kwargs['url_slug'],
                                 base_course__url_slug=self.kwargs['base_url_slug'])


class CourseDetailView(CourseMixin, DetailView):
    model = Course
    slug_field = "url_slug"
    slug_url_kwarg = "url_slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['teacher'] = context['course'].is_teacher(self.request.user)
        context['enrolled'] = context['course'].is_enrolled(self.request.user)
        return context


class CourseTeacherView(IsTeacherMixin, CourseDetailView):
    template_name = "courses/teacher.html"


class CourseUpdateView(CourseMixin, IsTeacherMixin, UpdateView):
    model = Course
    fields = ['start_date', 'end_date', 'aplus_apikey']
    # 403 if not teacher


class CourseListView(ListView):
    model = Course


class CourseEnroll(CourseMixin, LoginRequiredMixin, ProcessFormView):
    model = Course

    def get_success_url(self):
        return reverse("courses:detail", kwargs={'url_slug': self.kwargs['url_slug'],
                       'base_url_slug': self.kwargs['base_url_slug']})

    def post(self, request, *args, **kwargs):
        course = self.get_object()

        if course.can_enroll(self.request.user):
            course.enroll(self.request.user)
            messages.info(request, "You're now enrolled into the course.")
        else:
            messages.error(request, "You cannot enroll to this course.")

        return HttpResponseRedirect(reverse("courses:detail", kwargs={'url_slug': self.kwargs['url_slug'],
                                    'base_url_slug': self.kwargs['base_url_slug']}))

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse("courses:detail", kwargs={'url_slug': self.kwargs['url_slug'],
                                    'base_url_slug': self.kwargs['base_url_slug']}))
