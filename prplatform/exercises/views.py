from django.views.generic import DetailView, CreateView, ListView, TemplateView, UpdateView
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.forms import Textarea
from django.forms.models import modelform_factory

from .models import SubmissionExercise, BaseExercise
from .forms import SubmissionExerciseForm
from prplatform.courses.views import CourseContextMixin, IsTeacherMixin


class SubmissionExerciseDetailView(CourseContextMixin, DetailView):
    model = SubmissionExercise


class ExerciseCreateView(IsTeacherMixin, CourseContextMixin, TemplateView):
    """ TODO:
        This now lets the template to show the teacher multiple
        different exercise form types. Should they all have their
        different CreateViews or should they be included in the same
        view with some toggles?
    """
    # template_name = "exercises/create.html"

    def get(self, *args, **kwargs):
        """ TODO: currently returns only generalForm """
        context = self.get_context_data(**kwargs)
        context['generalForm'] = SubmissionExerciseForm()
        return self.render_to_response(context)

    def post(self, *args, **kwargs):
        """ TODO: error checking """
        form = SubmissionExerciseForm(self.request.POST)
        context = self.get_context_data()
        if form.is_valid():
            data = form.cleaned_data
            exer = SubmissionExercise(
                    name=data['name'],
                    course=context['course']
                    )
            exer.save()
            return HttpResponseRedirect(reverse('courses:teacher', kwargs=kwargs))


class SubmissionExerciseCreateView(ExerciseCreateView):
    model = SubmissionExercise
    template_name = "exercises/submissionexercise_create.html"


class SubmissionExerciseUpdateView(IsTeacherMixin, CourseContextMixin, UpdateView):
    model = SubmissionExercise
    form_class = SubmissionExerciseForm


class ExerciseListView(ListView):
    model = BaseExercise

