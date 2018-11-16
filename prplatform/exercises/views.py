from django.views.generic import DetailView, CreateView, UpdateView
from django.views.generic.edit import DeleteView
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.core.exceptions import EmptyResultSet, PermissionDenied
from django.contrib import messages
from django.forms import formset_factory

from prplatform.courses.models import Course
from .models import SubmissionExercise, ReviewExercise
from .question_models import Question
from .forms import SubmissionExerciseForm, ReviewExerciseForm, ChooseForm

from prplatform.courses.views import CourseContextMixin, IsTeacherMixin, IsEnrolledMixin, GroupMixin
from prplatform.submissions.forms import OriginalSubmissionForm, AnswerModelForm
from prplatform.submissions.models import OriginalSubmission, ReviewSubmission, Answer, ReviewLock


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
            return HttpResponseRedirect(reverse('courses:detail', kwargs=kwargs))

        else:
            return self.form_invalid(form)


class ReviewExerciseCreateView(IsTeacherMixin, CourseContextMixin, CreateView):
    template_name = "exercises/reviewexercise_create.html"
    form_class = ReviewExerciseForm
    initial = {
       'opening_time': timezone.now(),
       'closing_time': timezone.now(),
    }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['course'] = Course.objects.get(
                base_course__url_slug=self.kwargs['base_url_slug'],
                url_slug=self.kwargs['url_slug'])
        return kwargs

    def post(self, *args, **kwargs):
        """ TODO: error checking """
        self.object = None
        course = self.get_context_data()['course']

        form = ReviewExerciseForm(self.request.POST, course=course)

        if form.is_valid():  # and formset.is_valid():
            exer = form.save(commit=False)
            exer.course = course
            exer.question_order = []
            exer.save()

            return HttpResponseRedirect(reverse('courses:detail', kwargs=kwargs))

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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['course'] = Course.objects.get(
                base_course__url_slug=self.kwargs['base_url_slug'],
                url_slug=self.kwargs['url_slug'])
        return kwargs


###
#
# DETAIL VIEWS
#

class SubmissionExerciseDetailView(GroupMixin, CourseContextMixin, DetailView):

    model = SubmissionExercise

    # TODO: restrict submissions by both opening AND closing times
    #       refactor the logic to a class method instead of inlining it here

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        exercise = self.object
        user = self.request.user
        ctx = self.get_context_data(**kwargs)
        ctx['disable_form'] = False

        if not exercise.can_access(user):
            raise PermissionDenied

        if not exercise.can_submit(user) or ctx['teacher']:
            ctx['disable_form'] = True

        ctx['my_submissions'] = exercise.submissions_by_submitter(user)
        ctx['form'] = OriginalSubmissionForm(type=self.object.type, filetypes=self.object.accepted_filetypes)

        return self.render_to_response(ctx)

    def post(self, *args, **kwargs):
        """ TODO: error checking """
        self.object = self.get_object()
        ctx = self.get_context_data()
        exercise = self.object
        user = self.request.user

        if not exercise.can_submit(user):
            messages.error(self.request, 'You cannot submit.')
            ctx['disable_form'] = True
            return self.render_to_response(ctx)

        type = exercise.type
        form = OriginalSubmissionForm(self.request.POST, self.request.FILES, type=type)

        form.accepted_filetypes = None
        if exercise.type == SubmissionExercise.FILE_UPLOAD:
            # this value is set so that it is available in form.clean()
            # which is called inside is_valid()
            form.accepted_filetypes = exercise.accepted_filetypes

        if form.is_valid():
            # this initializes a new OriginalSubmission object object
            # --> after injecting the ForeignKey course it is safe to save
            sub = form.save(commit=False)
            sub.course = ctx['course']
            sub.exercise = exercise
            sub.submitter_user = user
            if exercise.use_groups:
                sub.submitter_group = ctx['my_group']
            if exercise.use_states:
                sub.state = OriginalSubmission.SUBMITTED
            sub.save()
            messages.success(self.request, 'Submission successful! You may see it below.')
            return redirect(sub)

        ctx['form'] = form
        return self.render_to_response(ctx)


class ReviewExerciseDetailView(IsEnrolledMixin, GroupMixin, CourseContextMixin, DetailView):
    model = ReviewExercise

    def _get_answer_modelforms(self, exercise):
        # this gathers all the teacher-chosen questions that
        # the peer-reviewing student will answer
        forms = []
        sorted_questions = exercise.question_list_in_order()
        for index, q in enumerate(sorted_questions):
            forms.append(AnswerModelForm(question=q))
        return forms

    def _get_teacher_random(self, ctx, exercise):
        # PLEASE NOTE:
        # order_by('?') can become _SLOW_ if the queryset returned is big enough
        reviewable = exercise.reviewable_exercise.submissions.order_by('?').first()
        if reviewable:
            ctx['reviewable'] = reviewable
            ctx['filecontents'] = reviewable.filecontents_or_none()
        my_submission = exercise.reviewable_exercise.submissions.order_by('?').first()
        if my_submission:
            ctx['my_submission'] = my_submission
            ctx['my_filecontents'] = my_submission.filecontents_or_none()
        return ctx

    def _get_random_ctx(self, ctx):
        user = self.request.user
        exercise = self.object

        if ctx['teacher']:
            return self._get_teacher_random(ctx, exercise)

        if ctx['my_submission']:
            ctx['my_filecontents'] = ctx['my_submission'].filecontents_or_none()

        rlock = None
        if exercise.use_groups:
            rlock_list = ReviewLock.objects.filter(group=ctx['my_group'], review_exercise=exercise)
        else:
            rlock_list = ReviewLock.objects.filter(user=user, review_exercise=exercise)

        if rlock_list:
            last_rlock = rlock_list.last()

            if last_rlock.review_submission and exercise.max_submission_count == len(rlock_list):
                ctx['reviews_done'] = True
                return ctx
            elif not last_rlock.review_submission:
                rlock = last_rlock

        if not rlock:
            # TODO: can field errors be raised from something not thought about here?
            #       is it a good idea to determine possible reviewables in the creation
            #       of the reviewlock?
            try:
                if exercise.use_groups:
                    rlock = ReviewLock.objects.create_rlock(exercise, self.request.user, group=ctx['my_group'])
                else:
                    rlock = ReviewLock.objects.create_rlock(exercise, self.request.user)
            except EmptyResultSet:  # nothing to review just yet
                rlock = None

        ctx['reviewable'] = rlock.original_submission if rlock else None
        if rlock and rlock.original_submission:
            ctx['filecontents'] = rlock.original_submission.filecontents_or_none()
        return ctx

    def _get_choose_ctx(self, ctx):

        sid = self.request.GET.get('choice')
        if sid:
            cf = ChooseForm(self.request.GET, exercise=self.object, user=self.request.user)
            if not cf.is_valid():
                raise PermissionDenied
            ctx['reviewable'] = OriginalSubmission.objects.get(id=sid)

            previous_reviews = self.object.submissions_by_submitter(self.request.user)
            if previous_reviews.filter(reviewed_submission__pk=ctx['reviewable'].pk):
                ctx['prev_review_exists'] = True

        ctx['chooseForm'] = cf if sid else ChooseForm(exercise=self.object, user=self.request.user)
        return ctx

    def get_context_data(self, *args, **kwargs):
        self.object = self.get_object()
        exercise = self.object
        ctx = super().get_context_data(**kwargs)

        if not ctx['teacher'] and not exercise.visible_to_students:
            raise PermissionDenied

        ctx['forms'] = self._get_answer_modelforms(exercise)
        ctx['my_submission'] = exercise.original_submissions_by(self.request.user).first()
        ctx['disable_form'] = True

        can_submit, errormsg = exercise.can_submit(self.request.user)

        if not can_submit:
            ctx['errormsg'] = errormsg
            return ctx

        if exercise.type == ReviewExercise.RANDOM:
            ctx = self._get_random_ctx(ctx)
        elif exercise.type == ReviewExercise.CHOOSE:
            ctx = self._get_choose_ctx(ctx)

        ctx['show_content_to_review'] = True
        if ctx['reviewable'] and not ctx['teacher']:
            ctx['disable_form'] = False

        return ctx

    def _post_random(self, ctx):
        # TODO: should it be possible to update the previous review submission?
        rlock_list = ReviewLock.objects.filter(user=self.request.user, review_exercise=self.object)
        rlock = rlock_list.last()

        new_review_submission = ReviewSubmission(course=ctx['course'],
                                                 submitter_user=self.request.user,
                                                 exercise=self.object,
                                                 reviewed_submission=rlock.original_submission)
        if self.object.use_groups:
            new_review_submission.submitter_group = ctx['my_group']

        new_review_submission.save()

        rlock.review_submission = new_review_submission
        rlock.save()

        self._save_modelform_answers(new_review_submission)
        return HttpResponseRedirect(new_review_submission.get_absolute_url())

    def _post_choose(self, ctx):

        cf = ChooseForm(self.request.POST, exercise=self.object, user=self.request.user)
        if not cf.is_valid():
            raise PermissionDenied('You cannot do that. If you believe this is an error, contact pietari.heino@tut.fi')

        # if ChooseForm is valid, construct a new ReviewSubmission
        reviewed_submission = OriginalSubmission.objects.get(pk=self.request.POST.get('choice'))
        new_review_submission = ReviewSubmission(course=ctx['course'],
                                                 submitter_user=self.request.user,
                                                 exercise=self.object,
                                                 reviewed_submission=reviewed_submission)
        if self.object.use_groups:
            new_review_submission.submitter_group = ctx['my_group']

        new_review_submission.save()
        self._save_modelform_answers(new_review_submission)
        return HttpResponseRedirect(new_review_submission.get_absolute_url())

    def _save_modelform_answers(self, review_submission):
        for form in self.forms:
            answer = form.save(commit=False)
            answer.submission = review_submission
            answer.save()

    def _validate_forms(self):
        qlist = self.object.question_list_in_order()

        forms = []
        valid = True
        for q in qlist:
            af = AnswerModelForm(self.request.POST, self.request.FILES, question=q)
            forms.append(af)
            if not af.is_valid():
                valid = False
        return valid, forms

    def post(self, *args, **kwargs):
        # TODO: error checking, validation(?)
        self.object = self.get_object()
        ctx = self.get_context_data(**kwargs)

        valid, self.forms = self._validate_forms()

        if not valid:
            ctx['forms'] = self.forms
            return self.render_to_response(ctx)

        if self.object.type == ReviewExercise.RANDOM:
            return self._post_random(ctx)

        elif self.object.type == ReviewExercise.CHOOSE:
            return self._post_choose(ctx)


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
