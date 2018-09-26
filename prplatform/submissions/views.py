from django.core.exceptions import PermissionDenied
from django import forms
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

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
        exercise = SubmissionExercise.objects.get(pk=self.kwargs['pk'])
        self.object_list = exercise.submissions.all()
        ctx = super().get_context_data(**self.kwargs)

        if not ctx['teacher']:
            # TODO: this is ugly as hell
            if exercise.use_groups:
                self.object_list = self.object_list.filter(submitter_group=exercise.course.find_studentgroup_by_user(self.request.user))
            else:
                self.object_list = self.object_list.filter(submitter_user=self.request.user)

        ctx['exercise'] = exercise
        ctx['originalsubmission_list'] = self.object_list
        return ctx


class ReviewSubmissionListView(IsEnrolledMixin, CourseContextMixin, ListView):
    model = ReviewSubmission

    def get_context_data(self):
        exercise = ReviewExercise.objects.get(pk=self.kwargs['pk'])
        self.object_list = exercise.submissions.all()
        ctx = super().get_context_data(**self.kwargs)

        my_group = exercise.course.find_studentgroup_by_user(self.request.user)

        if self.request.GET.get('mode') == "my":
            ctx['my_mode'] = True
            if exercise.use_groups:
                self.object_list = self.object_list.filter(reviewed_submission__submitter_group=my_group)
            else:
                self.object_list = self.object_list.filter(reviewed_submission__submitter_user=self.request.user)
        else:
            if not ctx['teacher']:
                if exercise.use_groups:
                    self.object_list = self.object_list.filter(submitter_group=my_group)
                else:
                    self.object_list = self.object_list.filter(submitter_user=self.request.user)

        ctx['exercise'] = exercise
        ctx['reviewsubmission_list'] = self.object_list
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

        data = []

        for ans in self.object.answers_in_ordered_list():
            if ans.question.hide_from_receiver and not ctx['teacher']:
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

