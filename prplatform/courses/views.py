from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView

from .models import Course
from prplatform.users.models import User


class CourseDetailView(DetailView):
    model = Course
    # slug_field = "name"
    # lug_url_kwarg = "name"


class CourseCreateView(CreateView):
    model = Course
    fields = ['name', 'code', 'url_slug', 'school']

    # def get_success_url(self):
    #     return reverse("courses:detail", kwargs={"name": self.request.course.name})

    def form_valid(self, form):
        form.instance.save()
        user = User.objects.get(email=self.request.user.email)
        form.instance.teachers.add(user)
        return super(CourseCreateView, self).form_valid(form)


class CourseListView(ListView):
    model = Course
