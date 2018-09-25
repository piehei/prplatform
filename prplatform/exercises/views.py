from django.views.generic import DetailView, CreateView, UpdateView
from django.views.generic.edit import DeleteView
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.core.exceptions import FieldError, PermissionDenied
from django.contrib import messages

import re

from .models import SubmissionExercise, ReviewExercise
from .question_models import Question
from .forms import SubmissionExerciseForm, ReviewExerciseForm, QuestionModelFormSet

from prplatform.courses.views import CourseContextMixin, IsTeacherMixin, IsEnrolledMixin, GroupMixin
from prplatform.submissions.forms import OriginalSubmissionForm, AnswerForm
from prplatform.submissions.models import ReviewSubmission, Answer, ReviewLock


###
#
# CREATE VIEWS
#

class SubmissionExerciseCreateView(IsTeacherMixin, CourseContextMixin, CreateView):
    model = SubmissionExercise
    template_name = "exercises/submissionexercise_create.html"
    form_class = SubmissionExerciseForm
    initial = {
            'opening_time': timezone.now(),
            'closing_time': timezone.now(),
            }

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
        context['form'] = ReviewExerciseForm(initial={
                                                'opening_time': timezone.now(),
                                                'closing_time': timezone.now(),
                                            })

        # TODO: first the teacher creates the exercise, then questions are added
        # qs = QuestionModelFormSet(queryset=Question.objects.none())
        # context['formset'] = qs

        return self.render_to_response(context)

    def post(self, *args, **kwargs):
        """ TODO: error checking """
        self.object = None
        course = self.get_context_data()['course']

        form = ReviewExerciseForm(self.request.POST)
        # formset = QuestionModelFormSet(self.request.POST)

        if form.is_valid():  # and formset.is_valid():
            # this initializes a new ReviewExercise object
            # --> after injecting the ForeignKey course it is safe to save
            exer = form.save(commit=False)
            exer.course = course
            exer.save()

            # for q in formset.ordered_forms:
                # q.instance.order = q.cleaned_data['ORDER']
                # q.instance.exercise = exer

            # formset.save()

            return HttpResponseRedirect(reverse('courses:teacher', kwargs=kwargs))

        else:
            ctx = self.get_context_data(**kwargs)
            ctx['form'] = form
            # ctx['formset'] = formset
            return self.render_to_response(ctx)

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
        # qs = QuestionModelFormSet(queryset=Question.objects.filter(exercise=self.object).order_by('order'))
        # context['formset'] = qs
        return self.render_to_response(context)

    def post(self, *args, **kwargs):
        """ TODO: error checking """
        self.object = self.get_object()

        r_exercise_form = self.get_form()  # returns the bound form instance with updated fields

        if r_exercise_form.is_valid():
            r_exercise = r_exercise_form.save()
            # question_formset = QuestionModelFormSet(self.request.POST)

            # TODO:
            # järjestyksen näyttäminen onnistuu nyt
            # mutta tallennuksessa ei ole validointia
            # overridaa valid, jotta virhe voidaan näyttää
            # lue ero modelformset ja inline_formset jne.

            # if question_formset.is_valid():
            #     question_formset.save(commit=False)
            #     # update the order values of the question objects
            #     # and make sure they reference the correct exercise object
            #     for q_form in question_formset.ordered_forms:
            #         q_form.instance.course = self.object.course
            #         # q_form.instance.exercise.add(r_exercise)
            #         q_form.instance.order = q_form.cleaned_data['ORDER']

            #     # this saves the Question model objects created and/or modified by
            #     # the POSTed formset
            #     # this takes care of deletion and not saving empty Question forms

            #     for saved_q in question_formset.save():
            #         print(saved_q)
            #         print(saved_q.course)
            #         r_exercise.questions.add(saved_q)
            return HttpResponseRedirect(reverse('courses:exercises:review-detail', kwargs=kwargs))


###
#
# DETAIL VIEWS
#

class SubmissionExerciseDetailView(IsEnrolledMixin, GroupMixin, CourseContextMixin, DetailView):

    model = SubmissionExercise

    # TODO: restrict submissions by both opening AND closing times
    #       refactor the logic to a class method instead of inlining it here

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        exercise = self.object
        user = self.request.user
        ctx = self.get_context_data(**kwargs)

        if not ctx['teacher'] and not exercise.visible_to_students:
            raise PermissionDenied

        ctx['my_submissions'] = exercise.submissions_by_submitter(user)

        if not exercise.can_submit(user):
            ctx['disable_form'] = True

        ctx['form'] = OriginalSubmissionForm(type=self.object.type, filetypes=self.object.accepted_file_types)

        return self.render_to_response(ctx)

    def post(self, *args, **kwargs):
        """ TODO: error checking """
        self.object = self.get_object()
        ctx = self.get_context_data()

        user = self.request.user
        course = ctx['course']
        exercise = self.object
        teacher = exercise.is_teacher(user)

        # TODO: teacher has to be able to override this!??!?!
        if not teacher and exercise.closing_time < timezone.now():
            messages.error(self.request, 'Closing time for the exercise has passed. You cannot submit.')
            ctx['disable_form'] = True
            return self.render_to_response(ctx)
        if not exercise.can_submit(user):
            messages.error(self.request, 'You have used all your submissions.')
            ctx['disable_form'] = True
            return self.render_to_response(ctx)

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
            sub = form.save(commit=False)
            sub.course = course
            sub.exercise = exercise
            sub.submitter_user = user
            if exercise.use_groups:
                sub.submitter_group = course.find_studentgroup_by_user(user)
            sub.save()
            messages.success(self.request, 'Submission successful! You may see it below.')
            return redirect(sub)

        ctx['form'] = form
        return self.render_to_response(ctx)


class ReviewExerciseDetailView(IsEnrolledMixin, CourseContextMixin, DetailView):
    model = ReviewExercise
    PREFIX = "question-index-"

    def _get_answer_forms(self):
        # this gathers all the teacher-chosen questions that
        # the peer-reviewing student will answer
        print(self.object.questions.all())
        forms = []
        for index, q in enumerate(self.object.questions.all()):
            print(index)
            print(q)
            print(q.text)
            print(q.choices.all())
            forms.append(AnswerForm(prefix=self.PREFIX + str(index),
                                    question_text=q.text,
                                    question_choices=q.choices.all()))
        print(forms)

        return forms

    def _render_teacher_view(self, ctx, exercise):
        reviewable = exercise.reviewable_exercise.submissions.first()
        if reviewable:
            ctx['reviewable'] = reviewable
            ctx['filecontents'] = reviewable.filecontents_or_none()

        my_submission = exercise.reviewable_exercise.submissions.last()
        if my_submission:
            ctx['my_submission'] = my_submission
            ctx['my_filecontents'] = my_submission.filecontents_or_none()

        return self.render_to_response(ctx)

    def get(self, *args, **kwargs):

        self.object = self.get_object()

        ctx = self.get_context_data(**kwargs)
        is_teacher = ctx['teacher']
        user = self.request.user
        exercise = self.get_object()

        if not is_teacher and not exercise.visible_to_students:
            raise PermissionDenied

        ctx['forms'] = self._get_answer_forms()

        if is_teacher:
            self._render_teacher_view(ctx, exercise)

        my_submission_qs = exercise.reviewable_exercise.submissions_by_submitter(user)
        if not my_submission_qs:
            return self.render_to_response(ctx)

        ctx['my_submission'] = my_submission_qs.first()
        ctx['my_filecontents'] = ctx['my_submission'].filecontents_or_none()

        rlock = None
        rlock_list = ReviewLock.objects.filter(user=user, review_exercise=exercise)

        # check if the user has review locks
        if rlock_list:
            last_rlock = rlock_list.last()

            # if last rlock has a ReviewSubmission and the user has done max num of reviews
            if last_rlock.review_submission and exercise.max_reviews_per_student == len(rlock_list):
                ctx['reviews_done'] = True
                return self.render_to_response(ctx)
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

        ctx['reviewable'] = reviewable

        if reviewable:
            ctx['filecontents'] = reviewable.filecontents_or_none()

        return self.render_to_response(ctx)

    def post(self, *args, **kwargs):
        # TODO: error checking, validation(?)
        self.object = self.get_object()
        ctx = self.get_context_data(**kwargs)
        course = ctx['course']
        exercise = self.object

        # TODO: should it be possible to update the previous review submission?
        rlock_list = ReviewLock.objects.filter(user=self.request.user, review_exercise=exercise)
        rlock = rlock_list.last()

        # TODO: this crashes when teacher submits since there's no release lock
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
