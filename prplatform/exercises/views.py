from django.views.generic import DetailView, CreateView, ListView, TemplateView, UpdateView
from django.views.generic.edit import DeleteView
from django.urls import reverse, resolve, reverse_lazy
from django.http import HttpResponseRedirect
from django.forms import Textarea
from django.forms.models import modelform_factory

from .models import SubmissionExercise, ReviewExercise
from .forms import SubmissionExerciseForm, ReviewExerciseForm, QuestionFormSet

from prplatform.courses.views import CourseContextMixin, IsTeacherMixin
from prplatform.submissions.forms import OriginalSubmissionForm

###
#
# CREATE VIEWS
#


class SubmissionExerciseCreateView(IsTeacherMixin, CourseContextMixin, CreateView):
    model = SubmissionExercise
    template_name = "exercises/submissionexercise_create.html"
    form_class = SubmissionExerciseForm

    def post(self, *args, **kwargs):
        """ TODO: error checking """
        form = SubmissionExerciseForm(self.request.POST)
        self.object = None # TODO: WTF ?????????????????????????????????????????????
        course = self.get_context_data()['course']

        if form.is_valid():
            # this initializes a new SubmissionExercise object
            # --> after injecting the ForeignKey course it is safe to save
            exer = form.save(commit=False)
            exer.course = course
            exer.save()
            return HttpResponseRedirect(reverse('courses:teacher', kwargs=kwargs))


class ReviewExerciseCreateView(IsTeacherMixin, CourseContextMixin, CreateView):
    template_name = "exercises/reviewexercise_create.html"
    form_class = QuestionFormSet

    def get(self, *args, **kwargs):
        self.object = None
        context = self.get_context_data(**kwargs)
        context['form'] = ReviewExerciseForm()
        context['formset'] = QuestionFormSet()

        return self.render_to_response(context)

    def post(self, *args, **kwargs):
        """ TODO: error checking """
        self.object = None
        course = self.get_context_data()['course']

        form = ReviewExerciseForm(self.request.POST)

        if form.is_valid():
            # this initializes a new ReviewExercise object
            # --> after injecting the ForeignKey course it is safe to save
            exer = form.save(commit=False)
            exer.course = course
            exer.save()

            formset = QuestionFormSet(self.request.POST, instance=exer)
            if formset.is_valid():
                formset.save()
                print("valid")

            return HttpResponseRedirect(reverse('courses:teacher', kwargs=kwargs))

###
#
# UPDATE VIEWS
#


class SubmissionExerciseUpdateView(IsTeacherMixin, CourseContextMixin, UpdateView):
    model = SubmissionExercise
    form_class = SubmissionExerciseForm


class ReviewExerciseUpdateView(IsTeacherMixin, CourseContextMixin, UpdateView):
    model = ReviewExercise
    form_class = ReviewExerciseForm

###
#
# DETAIL VIEWS
#


class SubmissionExerciseDetailView(CourseContextMixin, DetailView):

    model = SubmissionExercise

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)

        show_text = self.object.text
        show_file_upload = self.object.file_upload
        context['form'] = OriginalSubmissionForm(show_text=show_text, show_file_upload=show_file_upload)

        return self.render_to_response(context)

    def post(self, *args, **kwargs):
        """ TODO: error checking """
        self.object = self.get_object()
        context = self.get_context_data()

        show_text = self.object.text
        show_file_upload = self.object.file_upload
        form = OriginalSubmissionForm(self.request.POST, self.request.FILES, show_text=show_text,
                                      show_file_upload=show_file_upload)
        course = context['course']
        user = self.request.user

        if form.is_valid():
            # this initializes a new OriginalSubmission object object
            # --> after injecting the ForeignKey course it is safe to save
            exer = form.save(commit=False)
            exer.course = course
            exer.exercise = self.object
            exer.submitter = user
            exer.save()
            return HttpResponseRedirect(reverse('courses:detail', kwargs={
                    'base_url_slug': self.kwargs['base_url_slug'],
                    'url_slug': self.kwargs['url_slug']
                    }))

        context['form'] = form
        return self.render_to_response(context)

class ReviewExerciseDetailView(CourseContextMixin, DetailView):
    model = ReviewExercise

###
#
# DELETE VIEWS
#


class SubmissionExerciseDeleteView(CourseContextMixin, DeleteView):
    # TODO: check for submissions -> handle before deletion of the exercise
    model = SubmissionExercise

    def get_success_url(self):
        return reverse_lazy('courses:detail', kwargs={
            'base_url_slug': self.kwargs['base_url_slug'],
            'url_slug': self.kwargs['url_slug']
            })


class ReviewExerciseDeleteView(CourseContextMixin, DeleteView):
    # TODO: check for submissions -> handle before deletion of the exercise
    model = ReviewExercise

    def get_success_url(self):
        return reverse_lazy('courses:detail', kwargs={
            'base_url_slug': self.kwargs['base_url_slug'],
            'url_slug': self.kwargs['url_slug']
            })

