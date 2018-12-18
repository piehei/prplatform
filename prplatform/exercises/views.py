from django.contrib import messages
from django.core.exceptions import EmptyResultSet, PermissionDenied
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, CreateView, UpdateView
from django.views.generic.edit import DeleteView

from prplatform.courses.models import Course
from prplatform.courses.views import (
        CourseContextMixin,
        ExerciseContextMixin,
        GroupMixin,
        IsTeacherMixin,
    )
from prplatform.submissions.forms import (
        AnswerModelForm,
        OriginalSubmissionForm,
    )
from prplatform.submissions.models import (
        OriginalSubmission,
        ReviewSubmission,
    )
from prplatform.submissions.reviewlock_models import ReviewLock

from .models import (
        ReviewExercise,
        SubmissionExercise,
    )
from .forms import (
        ChooseForm,
        ReviewExerciseForm,
        SubmissionExerciseForm,
    )
from . import utils


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

    def form_valid(self, form):
        exercise = form.save(commit=False)
        exercise.course = self.get_context_data()['course']
        exercise.save()
        return super().form_valid(form)


class ReviewExerciseCreateView(IsTeacherMixin, CourseContextMixin, CreateView):
    template_name = "exercises/reviewexercise_create.html"
    form_class = ReviewExerciseForm
    initial = {
       'opening_time': timezone.now(),
       'closing_time': timezone.now(),
    }

    def get_initial(self):
        initial = self.initial.copy()
        # this pre-selects the SubmissionExercise for this new ReviewExercise
        reviewable_exercise_id = self.request.GET.get('subid', None)
        if reviewable_exercise_id:
            initial['reviewable_exercise'] = reviewable_exercise_id
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['course'] = Course.objects.get(
                base_course__url_slug=self.kwargs['base_url_slug'],
                url_slug=self.kwargs['url_slug'])
        return kwargs

    def form_valid(self, form):
        exercise = form.save(commit=False)
        exercise.course = self.get_context_data()['course']
        exercise.question_order = []
        exercise.save()
        return super().form_valid(form)

###
#
# UPDATE VIEWS
#


class SubmissionExerciseUpdateView(IsTeacherMixin, ExerciseContextMixin, UpdateView):
    model = SubmissionExercise
    form_class = SubmissionExerciseForm


class ReviewExerciseUpdateView(IsTeacherMixin, ExerciseContextMixin, UpdateView):
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

# TODO FIX ME
# needed for LTI posting, could it be done in some other way??????? this is not secure
class SubmissionExerciseDetailView(GroupMixin, ExerciseContextMixin, DetailView):

    model = SubmissionExercise

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(self.request, 'LTI_MODE'):
            self.request.LTI_MODE = False
        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        ctx = self.get_context_data(**kwargs)
        ctx['template_base'] = "base.html"
        ctx['disable_form'] = False

        if not self.object.can_submit(self.request.user) or ctx['teacher']:
            ctx['disable_form'] = True

        ctx['my_submissions'] = self.object.submissions_by_submitter(self.request.user)
        ctx['form'] = OriginalSubmissionForm(type=self.object.type, filetypes=self.object.accepted_filetypes)

        if self.request.LTI_MODE:
            ctx['APLUS_POST_URL'] = self.request.GET.get('post_url')
            ctx['embedded'] = True
            ctx['template_base'] = "base_embedded.html"

        return self.render_to_response(ctx)

    def post(self, *args, **kwargs):
        """ TODO: error checking """
        self.object = self.get_object()
        ctx = self.get_context_data()
        ctx['template_base'] = "base.html"
        exercise = self.object
        user = self.request.user

        if not self.request.LTI_MODE and not exercise.can_submit(user):
            messages.error(self.request, 'You cannot submit.')
            ctx['disable_form'] = True
            return self.render_to_response(ctx)

        form = OriginalSubmissionForm(self.request.POST, self.request.FILES, type=exercise.type)

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

            if self.request.LTI_MODE:
                return _construct_aplus_response()
            else:
                messages.success(self.request, 'Submission successful! You may see it below.')
                return redirect(sub)

        if self.request.LTI_MODE:
            return HttpResponse('An error occurred.')

        ctx['form'] = form
        return self.render_to_response(ctx)


def _construct_aplus_response():
    # TODO: teacher should be able to configure this
    response = HttpResponse(('<html>'
                             '<head>'
                             '<meta name="max-points" value="1" />'
                             '<meta name="points" value="1" />'
                             '</head>'
                             '<body>'
                             'Submission received!'
                             '</body>'
                             '</html>'))
    return response


class ReviewExerciseDetailView(GroupMixin, ExerciseContextMixin, DetailView):
    model = ReviewExercise

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(self.request, 'LTI_MODE'):
            self.request.LTI_MODE = False
        return super().dispatch(request, *args, **kwargs)

    def _get_answer_forms(self):
        forms = []
        for index, q in enumerate(self.object.question_list_in_order()):
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
        exercise = self.object

        if ctx['teacher']:
            return self._get_teacher_random(ctx, exercise)

        if ctx['my_submission']:
            ctx['my_filecontents'] = ctx['my_submission'].filecontents_or_none()

        rlock = exercise.reviewlocks_for(self.request.user).last()

        # if rlock doesn't exist or it exists and has a review attached
        if not rlock or \
           rlock and rlock.review_submission is not None:
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

    def _get_choose_ctx(self, ctx, groups=False):

        sid = self.request.GET.get('choice')
        if sid:
            cf = ChooseForm(self.request.GET, exercise=self.object, user=self.request.user)
            if not cf.is_valid():
                raise PermissionDenied('Dot\'t do that. Just don\'t.')
            ctx['reviewable'] = OriginalSubmission.objects.get(id=sid)

            previous_reviews = self.object.submissions_by_submitter(self.request.user)
            if previous_reviews.filter(reviewed_submission__pk=ctx['reviewable'].pk):
                ctx['prev_review_exists'] = True

        ctx['chooseForm'] = cf if sid else ChooseForm(exercise=self.object, user=self.request.user)
        return ctx

    def get_context_data(self, *args, **kwargs):
        self.object = self.get_object()
        ctx = super().get_context_data(**kwargs)
        ctx['template_base'] = "base.html"

        ctx['forms'] = self._get_answer_forms()
        ctx['my_submission'] = self.object.original_submissions_by(self.request.user).first()
        ctx['disable_form'] = True

        can_submit, errormsg = self.object.can_submit(self.request.user)

        if self.request.LTI_MODE:
            ctx['APLUS_POST_URL'] = self.request.GET.get('post_url')
            ctx['enrolled'] = True
            self.template_name = "exercises/reviewexercise_detail_embed.html"

        if not can_submit:
            ctx['errormsg'] = errormsg
            return ctx

        if self.object.type == ReviewExercise.RANDOM:
            ctx = self._get_random_ctx(ctx)
        elif self.object.type == ReviewExercise.CHOOSE:
            ctx = self._get_choose_ctx(ctx)
        elif self.object.type == ReviewExercise.GROUP:
            utils.prepare_group_review_exercise_for(self.object, self.request.user)
            ctx = self._get_choose_ctx(ctx)

        ctx['show_content_to_review'] = True
        if ctx['reviewable'] and not ctx['teacher']:
            ctx['disable_form'] = False

        return ctx

    def _post_random(self, ctx):
        # TODO: should it be possible to update the previous review submission?
        rlock_list = self.object.reviewlocks_for(self.request.user)
        rlock = rlock_list.last()

        new_review_submission = ReviewSubmission(course=ctx['course'],
                                                 submitter_user=self.request.user,
                                                 exercise=self.object,
                                                 reviewed_submission=rlock.original_submission)
        if self.object.use_groups:
            new_review_submission.submitter_group = ctx['my_group']

        new_review_submission.save_and_destroy_lock()

        self._save_modelform_answers(new_review_submission)

        if self.request.LTI_MODE:
            return _construct_aplus_response()
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

        can_submit, errormsg = self.object.can_submit(self.request.user)

        if not self.request.LTI_MODE and not can_submit:
            messages.error(self.request, 'You cannot submit.')
            ctx['disable_form'] = True
            return self.render_to_response(ctx)

        valid, self.forms = self._validate_forms()
        if not valid:
            ctx['forms'] = self.forms
            return self.render_to_response(ctx)

        if self.object.type == ReviewExercise.RANDOM:
            return self._post_random(ctx)

        elif self.object.type in [ReviewExercise.CHOOSE, ReviewExercise.GROUP]:
            return self._post_choose(ctx)


###
#
# DELETE VIEWS
#


class SubmissionExerciseDeleteView(IsTeacherMixin, ExerciseContextMixin, DeleteView):
    # TODO: check for submissions -> handle before deletion of the exercise
    model = SubmissionExercise

    def get_success_url(self):
        return reverse_lazy('courses:detail', kwargs={
            'base_url_slug': self.kwargs['base_url_slug'],
            'url_slug': self.kwargs['url_slug']
            })


class ReviewExerciseDeleteView(IsTeacherMixin, ExerciseContextMixin, DeleteView):
    # TODO: check for submissions -> handle before deletion of the exercise
    model = ReviewExercise

    def get_success_url(self):
        return reverse_lazy('courses:detail', kwargs={
            'base_url_slug': self.kwargs['base_url_slug'],
            'url_slug': self.kwargs['url_slug']
            })
