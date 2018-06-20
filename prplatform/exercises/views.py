from django.views.generic import DetailView, CreateView, UpdateView
from django.views.generic.edit import DeleteView
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponseServerError
from django.core.exceptions import FieldError

import re

from .models import SubmissionExercise, ReviewExercise, Question
from .forms import SubmissionExerciseForm, ReviewExerciseForm, QuestionModelFormSet

from prplatform.courses.views import CourseContextMixin, IsTeacherMixin, IsEnrolledMixin
from prplatform.submissions.forms import OriginalSubmissionForm, AnswerForm
from prplatform.submissions.models import OriginalSubmission, ReviewSubmission, Answer, ReviewLock
from prplatform.aplus_integration.core import get_submissions_by_id


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

        else:
            return self.form_invalid(form)


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

class SubmissionExerciseDetailView(IsEnrolledMixin, CourseContextMixin, DetailView):

    model = SubmissionExercise

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)

        my_submissions = self.object.submissions.filter(submitter=self.request.user)

        if len(my_submissions) > 0:
            context['my_submissions'] = my_submissions
            return self.render_to_response(context)


        type = self.object.type
        context['form'] = OriginalSubmissionForm(type=type)

        return self.render_to_response(context)

    def post(self, *args, **kwargs):
        """ TODO: error checking """
        self.object = self.get_object()
        context = self.get_context_data()

        user = self.request.user
        course = context['course']
        exercise = self.object

        type = exercise.type
        form = OriginalSubmissionForm(self.request.POST, self.request.FILES, type=type)

        form.accepted_file_types = None
        if exercise.type == SubmissionExercise.FILE_UPLOAD:
            # this value is set so that it is available in form.clean()
            # which is called inside is_valid()
            form.accepted_file_types = exercise.accepted_file_types

        if form.is_valid():
            # this initializes a new OriginalSubmission object object
            # --> after injecting the ForeignKey course it is safe to save
            exer = form.save(commit=False)
            exer.course = course
            exer.exercise = exercise
            exer.submitter = user
            exer.save()
            return HttpResponseRedirect(reverse('courses:detail', kwargs={
                    'base_url_slug': self.kwargs['base_url_slug'],
                    'url_slug': self.kwargs['url_slug']
                    }))

        context['form'] = form
        return self.render_to_response(context)


class ReviewExerciseDetailView(IsEnrolledMixin, CourseContextMixin, DetailView):
    model = ReviewExercise
    PREFIX = "question-index-"

    def get(self, *args, **kwargs):

        self.object = self.get_object()

        if self.object.reviewable_exercise.type == SubmissionExercise.APLUS:
            # TODO: this is not good way to check for errors etc.
            error = get_submissions_by_id(self.object.reviewable_exercise)
            if error:
                return HttpResponseServerError("APLUS APIKEY MISSING: teacher should add the apikey to the course's details")

        context = self.get_context_data(**kwargs)
        is_teacher = context['teacher']
        exercise = self.get_object()
        questions = exercise.questions.all()

        # this gathers all the teacher-chosen questions that
        # the peer-reviewing student will answer
        forms = []
        for index, q in enumerate(questions):
            # if previous_submission:
                # print(previous_submission.answers[index])
            forms.append(AnswerForm(prefix=self.PREFIX + str(index), question_text=q.text))
        context['forms'] = forms

        if is_teacher:

            reviewable = exercise.reviewable_exercise.submissions.first()
            context['reviewable'] = reviewable
            if reviewable.file:
                context['filecontents'] = reviewable.file.read().decode('utf-8')

            my_submission = exercise.reviewable_exercise.submissions.last()
            context['my_submission'] = my_submission
            if my_submission.file:
                context['my_filecontents'] = my_submission.file.read().decode('utf-8')

            return self.render_to_response(context)

        my_submission = exercise.reviewable_exercise.submissions.filter(submitter=self.request.user)
        if not my_submission:
            return self.render_to_response(context)

        my_submission = my_submission[0]
        context['my_submission'] = my_submission

        if my_submission.file:
            context['my_filecontents'] = my_submission.file.read().decode('utf-8')

        rlock = None
        rlock_list = ReviewLock.objects.filter(user=self.request.user, review_exercise=exercise)

        # check if the user has review locks
        if rlock_list:
            last_rlock = rlock_list.last()

            # if last rlock has a ReviewSubmission and the user has done max num of reviews
            if last_rlock.review_submission and exercise.review_count == len(rlock_list):
                context['reviews_done'] = True
                return self.render_to_response(context)
            elif not last_rlock.review_submission:
                # work on the last review lock
                rlock = last_rlock
            else:
                # user has no current rlocks -> continue and get a new one
                pass

        # this decides what to show to the student;
        # --> what is the thing that is going to get peer-reviewed

        reviewable = None if not rlock else rlock.original_submission

        if not rlock:
            # TODO: can field errors be raised from something not thought about here?
            #       is it a good idea to determine possible reviewables in the creation
            #       of the reviewlock?
            try:
                rlock = ReviewLock.objects.create_rlock(exercise, self.request.user)
                reviewable = rlock.original_submission
            except FieldError:
                pass

        context['reviewable'] = reviewable

        if reviewable and reviewable.file:
            context['filecontents'] = reviewable.file.read().decode('utf-8')

        return self.render_to_response(context)

    def post(self, *args, **kwargs):
        # TODO: error checking, validation(?)
        self.object = self.get_object()
        course = self.get_context_data(**kwargs)['course']
        exercise = self.object

        # TODO: should it be possible to update the previous review submission?
        rlock_list = ReviewLock.objects.filter(user=self.request.user, review_exercise=exercise)
        rlock = rlock_list.last()

        reviewed_submission = rlock.original_submission
        submission = ReviewSubmission.objects.create(course=course,
                                                     submitter=self.request.user,
                                                     exercise=exercise,
                                                     reviewed_submission=reviewed_submission)
        rlock.review_submission = submission
        rlock.save()

        questions = exercise.questions.all()

        for key in self.request.POST:
            print(key)
            if self.PREFIX not in key:
                continue
            indx = int(re.match(r".*(\d).*", key).groups()[0])
            q_now = questions[indx]
            Answer.objects.create(submission=submission,
                                  question=q_now,
                                  value=self.request.POST[key])

        return HttpResponseRedirect(reverse('courses:exercises:review-detail', kwargs=kwargs))

###
#
# DELETE VIEWS
#


class SubmissionExerciseDeleteView(IsTeacherMixin, CourseContextMixin, DeleteView):
    # TODO: check for submissions -> handle before deletion of the exercise
    model = SubmissionExercise

    def get_success_url(self):
        return reverse_lazy('courses:detail', kwargs={
            'base_url_slug': self.kwargs['base_url_slug'],
            'url_slug': self.kwargs['url_slug']
            })


class ReviewExerciseDeleteView(IsTeacherMixin, CourseContextMixin, DeleteView):
    # TODO: check for submissions -> handle before deletion of the exercise
    model = ReviewExercise

    def get_success_url(self):
        return reverse_lazy('courses:detail', kwargs={
            'base_url_slug': self.kwargs['base_url_slug'],
            'url_slug': self.kwargs['url_slug']
            })

