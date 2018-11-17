from django.views.generic import CreateView, ListView, DeleteView
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect
from prplatform.courses.views import CourseContextMixin, IsTeacherMixin
from prplatform.exercises.deviation_models import SubmissionExerciseDeviation
from prplatform.exercises.models import SubmissionExercise
from prplatform.courses.models import Course
from .deviation_forms import DeviationForm


class SEDeviationListView(IsTeacherMixin, CourseContextMixin, ListView):
    model = SubmissionExerciseDeviation

    def get_queryset(self):
        return super().get_queryset().filter(exercise=SubmissionExercise.objects.get(pk=self.kwargs['pk']))

    def get_context_data(self):
        ctx = super().get_context_data()
        ctx['exercise'] = SubmissionExercise.objects.get(pk=self.kwargs['pk'])
        return ctx


class SEDeviationCreateView(IsTeacherMixin, CourseContextMixin, CreateView):
    model = SubmissionExerciseDeviation
    form_class = DeviationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['exercise'] = SubmissionExercise.objects.get(pk=self.kwargs['pk'])
        kwargs['initial']['new_deadline'] = timezone.now()
        kwargs['initial']['exercise'] = kwargs['exercise']
        return kwargs

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data()
        ctx['exercise'] = SubmissionExercise.objects.get(pk=self.kwargs['pk'])
        return ctx

    def form_valid(self, form):

        deviation = form.save(commit=False)
        deviation.exercise = SubmissionExercise.objects.get(pk=self.kwargs['pk'])
        deviation.save()
        return HttpResponseRedirect(deviation.exercise.get_deviations_list_url())


class SEDeviationDeleteView(IsTeacherMixin, CourseContextMixin, DeleteView):
    model = SubmissionExerciseDeviation

    def get_success_url(self):
        return reverse('courses:exercises:submission-deviation-list', kwargs={
            'base_url_slug': self.kwargs['base_url_slug'],
            'url_slug': self.kwargs['url_slug'],
            'pk': self.kwargs['rpk']
            })

