from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView

from .models import BaseCourse, Course
from prplatform.users.models import User


class CourseDetailView(DetailView):
    model = Course
    slug_field = "url_slug"
    slug_url_kwarg = "url_slug"

    def get_absolute_url(self):
        return reverse('courses:detail', kwargs={'url_slug': self.request.url_slug})

    def get_object(self):
        base_course = get_object_or_404(BaseCourse, url_slug=self.kwargs['base_url_slug'])
        return get_object_or_404(Course, base_course=base_course, url_slug=self.kwargs['url_slug'])


class CourseUpdateView(UpdateView):
    model = Course
    fields = ['start_date', 'end_date']

    def get_object(self):
        base_course = get_object_or_404(BaseCourse, url_slug=self.kwargs['base_url_slug'])
        return get_object_or_404(Course, base_course=base_course, url_slug=self.kwargs['url_slug'])


class CourseCreateView(CreateView):
    model = Course
    fields = ['code', 'url_slug', 'start_date', 'end_date']
    template_name = "courses/course_create.html"

    def get_success_url(self):
        return reverse("courses:detail",
                kwargs={'url_slug': self.kwargs['url_slug'],
                        'base_url_slug': self.kwargs['base_url_slug'] })

    def form_valid(self, form):
        # form.instance.save()
        # user = User.objects.get(email=self.request.user.email)
        # form.instance.teachers.add(user)
        return super(CourseCreateView, self).form_valid(form)


class CourseListView(ListView):
    model = Course
