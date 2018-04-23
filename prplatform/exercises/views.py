from django.views.generic import DetailView, CreateView, ListView
from django.urls import reverse

from .models import BaseExercise

class ExerciseView(DetailView):
    model = BaseExercise


class ExerciseCreateView(CreateView):
    model = BaseExercise
    fields = ['name']

    def get_absolute_url(self):
        return reverse('courses:exercises:create', kwargs={'url_slug': self.url_slug,
                       'base_url_slug': self.base_course.url_slug})


class ExerciseListView(ListView):
    model = BaseExercise

