from django.views.generic import DetailView, CreateView, ListView, TemplateView, UpdateView
from django.urls import reverse
from django.http import HttpResponseRedirect

from .models import GeneralExercise, BaseExercise
from .forms import GeneralExerciseForm
from prplatform.courses.views import CourseContextMixin


class GeneralExerciseDetailView(CourseContextMixin, DetailView):
    model = GeneralExercise


class ExerciseCreateView(CourseContextMixin, TemplateView):
    """ TODO:
        This now lets the template to show the teacher multiple
        different exercise form types. Should they all have their
        different CreateViews or should they be included in the same
        view with some toggles?
    """
    template_name = "exercises/create.html"

    def get(self, *args, **kwargs):
        """ TODO: currently returns only generalForm """
        context = self.get_context_data(**kwargs)
        context['generalForm'] = GeneralExerciseForm()
        return self.render_to_response(context)

    def post(self, *args, **kwargs):
        """ TODO: error checking """
        form = GeneralExerciseForm(self.request.POST)
        context = self.get_context_data()
        if form.is_valid():
            data = form.cleaned_data
            exer = GeneralExercise(
                    name=data['name'],
                    course=context['course']
                    )
            exer.save()
            return HttpResponseRedirect(reverse('courses:teacher', kwargs=kwargs))


class GeneralExerciseCreateView(ExerciseCreateView):
    model = GeneralExercise


class GeneralExerciseUpdateView(CourseContextMixin, UpdateView):
    model = GeneralExercise
    fields = ['name', 'file_upload', 'upload_instructions', 'description']


class ExerciseListView(ListView):
    model = BaseExercise
