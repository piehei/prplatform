from django.core.exceptions import PermissionDenied
from django import forms
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

import os

from .models import OriginalSubmission, ReviewSubmission
from .forms import OriginalSubmissionStateForm

from prplatform.courses.views import CourseContextMixin, IsTeacherMixin, IsSubmitterOrTeacherMixin, IsEnrolledMixin
from prplatform.exercises.models import SubmissionExercise, ReviewExercise

###
#
# LIST VIEWS
#


class OriginalSubmissionListView(IsEnrolledMixin, CourseContextMixin, ListView):
    model = OriginalSubmission

    def get_context_data(self):
        ctx = super().get_context_data(**self.kwargs)
        ctx['exercise'] = SubmissionExercise.objects.get(pk=self.kwargs['pk'])
        if not ctx['teacher']:
            ctx['object_list'] = ctx['exercise'].submissions_by_submitter(self.request.user)
        return ctx


class ReviewSubmissionListView(IsEnrolledMixin, CourseContextMixin, ListView):
    model = ReviewSubmission

    def get_context_data(self):
        ctx = super().get_context_data(**self.kwargs)
        ctx['exercise'] = ReviewExercise.objects.get(pk=self.kwargs['pk'])

        if self.request.GET.get('mode') == "my":
            ctx['my_mode'] = True
            ctx['object_list'] = ctx['exercise'].last_reviews_for(self.request.user)
            if ctx['exercise'].show_reviews_after_date and ctx['exercise'].show_reviews_after_date > timezone.now():
                ctx['show_reviews_date_not_passed'] = True
        else:
            if not ctx['teacher']:
                ctx['object_list'] = ctx['exercise'].submissions_by_submitter(self.request.user)
        return ctx


###
#
# DETAIL VIEWS
#

class OriginalSubmissionDetailView(IsSubmitterOrTeacherMixin, CourseContextMixin, DetailView):
    model = OriginalSubmission
    pk_url_kwarg = "sub_pk"

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        ctx = self.get_context_data(**kwargs)

        ctx['filecontents'] = self.object.filecontents_or_none()

        if ctx['teacher'] and self.object.exercise.use_states:
            ctx['state_form'] = OriginalSubmissionStateForm(instance=self.object)
            ctx['other_submissions'] = self.object.submissions_by_same_submitter()

        return self.render_to_response(ctx)


class OriginalSubmissionUpdateView(IsTeacherMixin, CourseContextMixin, UpdateView):
    """
    The teacher can submit this form from the detail view of a submission.
    Using the form the teacher can either make the submission available in
    the pool of peer-review ready submissions (change state from 'SUBMITTED' to
    'READY_FOR_REVIEW') or give student(s) some feedback and request fixes with
    the 'BOOMERANG' state.
    """

    model = OriginalSubmission
    fields = ['state']

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        form = OriginalSubmissionStateForm(self.request.POST, instance=self.object)
        if form.is_valid():
            form.save()
            messages.success(self.request, 'The state of the submission has been updated')
        return redirect(self.object.get_absolute_url())


class ReviewSubmissionDetailView(LoginRequiredMixin, CourseContextMixin, DetailView):
    model = ReviewSubmission
    pk_url_kwarg = "sub_pk"

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        ctx = self.get_context_data(**kwargs)

        owner = self.object.is_owner(self.request.user)
        receiver = self.object.reviewed_submission.is_owner(self.request.user)

        if not owner and not receiver and not ctx['teacher']:
            raise PermissionDenied

        avail_date = self.object.exercise.show_reviews_after_date
        if avail_date and avail_date > timezone.now() and receiver:
            raise PermissionDenied(f'This will be available for viewing after {avail_date}')

        ctx['receiver'] = receiver

        data = []

        for ans in self.object.answers_in_ordered_list():
            if ans.question.hide_from_receiver and not owner and not ctx['teacher']:
                continue

            if ans.value_text:
                data.append({'q': ans.question.text, 'a': ans.value_text})
            else:
                # TODO : braindead ???
                choice = [c[1] for c in ans.question.choices if c[0] == ans.value_choice][0]
                data.append({'q': ans.question.text, 'a': choice})

        ctx['qa_list'] = data
        return self.render_to_response(ctx)


class DownloadSubmissionView(LoginRequiredMixin, View):

    def get(self, *args, **kwargs):
        user = self.request.user

        # user tries to download this
        obj = get_object_or_404(OriginalSubmission, pk=kwargs['pk'])
        teacher = obj.course.is_teacher(user)
        owner = obj.is_owner(user)

        pks_of_users_reviewables = user.reviewlock_set.all().values_list('original_submission', flat=True)
        reviewer = kwargs['pk'] in pks_of_users_reviewables

        if not teacher and not owner and not reviewer:
            raise PermissionDenied

        filename = obj.file.name.split('/')[-1]
        response = HttpResponse(obj.file, content_type='text/plain')

        # TODO: enough headers? meta type etc.?
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response

