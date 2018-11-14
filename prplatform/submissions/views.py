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

from .models import OriginalSubmission, ReviewSubmission, Answer
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
        ctx['object_list'] = ctx['exercise'].submissions.all()
        if not ctx['teacher']:
            ctx['object_list'] = ctx['exercise'].submissions_by_submitter(self.request.user)
        return ctx


class ReviewSubmissionListView(IsEnrolledMixin, CourseContextMixin, ListView):
    model = ReviewSubmission

    def get_context_data(self):
        ctx = super().get_context_data(**self.kwargs)
        ctx['exercise'] = ReviewExercise.objects.get(pk=self.kwargs['pk'])
        ctx['object_list'] = ctx['exercise'].submissions.all()

        if self.request.GET.get('mode') == "my":
            ctx['my_mode'] = True

            ctx['object_list'] = ctx['exercise'].last_reviews_for(self.request.user)

            print(ctx['object_list'])

            if ctx['exercise'].reviews_available_date_in_future():
                ctx['reviews_available_date_in_future'] = True
                ctx['object_list'] = ReviewSubmission.objects.none()

            if not ctx['exercise'].review_showing_requirements_ok(self.request.user):
                ctx['needs_to_complete_more_reviews'] = True
                ctx['object_list'] = ReviewSubmission.objects.none()

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
        ctx['receiver'] = self.object.reviewed_submission.is_owner(self.request.user)

        if not owner and not ctx['receiver'] and not ctx['teacher']:
            raise PermissionDenied

        if ctx['receiver']:
            if self.object.exercise.reviews_available_date_in_future():
                raise PermissionDenied(f'This is not available for your viewing just yet.')
            if not self.object.exercise.review_showing_requirements_ok(self.request.user):
                raise PermissionDenied('You have to complete more reviews to view this.')

        data = []

        for ans in self.object.answers_in_ordered_list():
            if ans.question.hide_from_receiver and not owner and not ctx['teacher']:
                continue

            if ans.value_text:
                data.append({'q': ans.question.question_text, 'a': ans.value_text})
            elif ans.value_choice:
                # TODO : braindead ???
                choice = [c[1] for c in ans.question.choices if c[0] == ans.value_choice][0]
                data.append({'q': ans.question.question_text, 'a': choice})
            else:
                data.append({'q': ans.question.question_text, 'f': ans.get_download_url()})

        ctx['qa_list'] = data
        return self.render_to_response(ctx)


class DownloadSubmissionView(IsEnrolledMixin, View):

    def get(self, *args, **kwargs):
        user = self.request.user

        dtype = 'answer' if self.request.GET.get('type') == 'answer' else 'osub'

        if dtype == 'answer':
            obj = get_object_or_404(Answer, pk=kwargs['pk'])
            teacher = obj.submission.course.is_teacher(user)
            owner = obj.submission.is_owner(user)
            re = obj.submission.exercise
            file_itself = obj.uploaded_file
        else:
            obj = get_object_or_404(OriginalSubmission, pk=kwargs['pk'])
            teacher = obj.course.is_teacher(user)
            owner = obj.is_owner(user)
            re = obj.exercise.review_exercise
            file_itself = obj.file

        enrolled_can_access = False
        if re and re.type == ReviewExercise.CHOOSE and dtype == 'osub':
            # anyone on the course can download anything
            enrolled_can_access = True

        reviewer = False
        receiver = False
        if dtype == 'osub':
            pks_of_users_reviewables = user.reviewlock_set.all().values_list('original_submission', flat=True)
            reviewer = kwargs['pk'] in pks_of_users_reviewables
        else:
            receiver = obj.submission.reviewed_submission.is_owner(user)

        if not teacher and not owner and not reviewer and not receiver and not enrolled_can_access:
            raise PermissionDenied

        filename = file_itself.name.split('/')[-1]
        response = HttpResponse(file_itself, content_type='text/plain')

        # TODO: enough headers? meta type etc.?
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response

