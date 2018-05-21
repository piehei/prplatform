from django.views.generic import DetailView, CreateView, ListView, UpdateView
from django.views.generic.edit import DeleteView
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.forms import formset_factory

import re

from .models import SubmissionExercise, ReviewExercise, Question
from .forms import SubmissionExerciseForm, ReviewExerciseForm, QuestionModelFormSet

from prplatform.courses.views import CourseContextMixin, IsTeacherMixin
from prplatform.submissions.forms import OriginalSubmissionForm, AnswerForm
from prplatform.submissions.models import ReviewSubmission, Answer



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
        self.object = None  # TODO: WTF ?????????????????????????????????????????????
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
    form_class = ReviewExerciseForm

    def get(self, *args, **kwargs):
        self.object = None
        context = self.get_context_data(**kwargs)
        context['form'] = ReviewExerciseForm()
        qs = QuestionModelFormSet(queryset=Question.objects.none())
        context['formset'] = qs

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

            formset = QuestionModelFormSet(self.request.POST)
            if formset.is_valid():
                for q in formset.ordered_forms:
                    q.instance.order = q.cleaned_data['ORDER']
                    q.instance.exercise = exer

                formset.save()

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

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        context['form'] = ReviewExerciseForm(instance=self.object)
        qs = QuestionModelFormSet(queryset=Question.objects.filter(exercise=self.object).order_by('order'))
        context['formset'] = qs
        return self.render_to_response(context)

    def post(self, *args, **kwargs):
        """ TODO: error checking """
        self.object = self.get_object()

        r_exercise_form = self.get_form()  # returns the bound form instance with updated fields

        if r_exercise_form.is_valid():
            r_exercise = r_exercise_form.save()
            question_formset = QuestionModelFormSet(self.request.POST)

            #TODO:
            # järjestyksen näyttäminen onnistuu nyt
            # mutta tallennuksessa ei ole validointia
            # overridaa valid, jotta virhe voidaan näyttää
            # lue ero modelformset ja inline_formset jne.

            if question_formset.is_valid():
                # update the order values of the question objects
                # and make sure they reference the correct exercise object
                for q_form in question_formset.ordered_forms:
                    q_form.instance.exercise = r_exercise
                    q_form.instance.order = q_form.cleaned_data['ORDER']

                # this saves the Question model objects created and/or modified by
                # the POSTed formset
                # this takes care of deletion and not saving empty Question forms
                question_formset.save()

            return HttpResponseRedirect(reverse('courses:exercises:review-detail', kwargs=kwargs))


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
    PREFIX = "question-index-"

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)

        forms = []

        exercise = self.get_object()
        questions = exercise.questions.all()

        for index, q in enumerate(questions):
            forms.append(AnswerForm(prefix=self.PREFIX + str(index), question_text=q.text))

        context['forms'] = forms

        return self.render_to_response(context)

    def post(self, *args, **kwargs):
        # TODO: error checking, validation(?)
        self.object = self.get_object()
        course = self.get_context_data(**kwargs)['course']
        exercise = self.object

        submission = ReviewSubmission(course=course,
                                      submitter=self.request.user,
                                      exercise=exercise)
        submission.save()

        questions = exercise.questions.all()

        for key in self.request.POST:
            print(key)
            if self.PREFIX not in key:
                continue
            indx = int(re.match(r".*(\d).*", key).groups()[0])
            q_now = questions[indx]
            a = Answer(submission=submission,
                       question=q_now,
                       value=self.request.POST[key])
            a.save()
        return HttpResponseRedirect(reverse('courses:exercises:review-detail', kwargs=kwargs))

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

