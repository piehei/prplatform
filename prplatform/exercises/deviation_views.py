from django.views.generic import CreateView, ListView, DeleteView
from django.forms import modelform_factory
from django.urls import reverse
from django.http import HttpResponseRedirect
from prplatform.courses.views import CourseContextMixin, IsTeacherMixin
from prplatform.exercises.deviation_models import SubmissionExerciseDeviation, ReviewExerciseDeviation
from prplatform.exercises.models import SubmissionExercise, ReviewExercise
from .deviation_forms import DeviationForm


class DeviationBaseView(object):
    ExerciseModel = None
    DeviationModel = None

    def dispatch(self, request, *args, **kwargs):
        if kwargs['deviation_type'] == 's':
            self.ExerciseModel = SubmissionExercise
            self.DeviationModel = SubmissionExerciseDeviation
            self.model = SubmissionExerciseDeviation
        else:
            self.ExerciseModel = ReviewExercise
            self.DeviationModel = ReviewExerciseDeviation
            self.model = ReviewExerciseDeviation

        return super().dispatch(request, args, kwargs)


class DeviationListView(IsTeacherMixin, CourseContextMixin, DeviationBaseView, ListView):

    template_name = 'exercises/deviation_list.html'

    def get_queryset(self):
        return self.DeviationModel.objects.filter(exercise=self.ExerciseModel.objects.get(pk=self.kwargs['pk']))

    def get_context_data(self):
        ctx = super().get_context_data()
        ctx['exercise'] = self.ExerciseModel.objects.get(pk=self.kwargs['pk'])
        return ctx


class DeviationCreateView(IsTeacherMixin, CourseContextMixin, DeviationBaseView, CreateView):
    template_name = 'exercises/deviation_form.html'

    def get_form_class(self):
        return modelform_factory(self.DeviationModel, form=DeviationForm)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['exercise'] = self.ExerciseModel.objects.get(pk=self.kwargs['pk'])
        kwargs['initial']['exercise'] = kwargs['exercise']
        return kwargs

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data()
        ctx['exercise'] = self.ExerciseModel.objects.get(pk=self.kwargs['pk'])
        return ctx

    def form_valid(self, form):

        deviation = form.save(commit=False)
        deviation.exercise = self.ExerciseModel.objects.get(pk=self.kwargs['pk'])
        deviation.save()
        return HttpResponseRedirect(deviation.exercise.get_deviations_list_url())


class DeviationDeleteView(IsTeacherMixin, CourseContextMixin, DeviationBaseView, DeleteView):

    def get_success_url(self):
        if self.kwargs['deviation_type'] == 's':
            typestr = 'submission'
        else:
            typestr = 'review'

        print(typestr)

        return reverse(f'courses:exercises:{typestr}-deviation-list', kwargs={
            'base_url_slug': self.kwargs['base_url_slug'],
            'url_slug': self.kwargs['url_slug'],
            'pk': self.kwargs['exer_pk']
            })

