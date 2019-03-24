from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from prplatform.courses.views import (
        CourseContextMixin,
        IsTeacherMixin,
        IsSubmitterOrTeacherMixin,
        IsEnrolledMixin,
    )
from prplatform.exercises.models import (
        SubmissionExercise,
        ReviewExercise,
    )

from .models import (
        Answer,
        DownloadToken,
        OriginalSubmission,
        ReviewSubmission,
    )
from .forms import OriginalSubmissionStateForm


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
        ctx['receiver'] = self.object.reviewed_submission.is_owner(self.request.user) and \
            not self.object.exercise.show_reviews_only_to_teacher

        if not owner and not ctx['receiver'] and not ctx['teacher']:
            raise PermissionDenied

        if ctx['receiver']:
            if self.object.exercise.reviews_available_date_in_future():
                raise PermissionDenied(f'This is not available for your viewing just yet.')
            if not self.object.exercise.review_showing_requirements_ok(self.request.user):
                raise PermissionDenied('You have to complete more reviews to view this.')

        ctx['qa_list'] = list(filter(
                lambda a: not (a.question.hide_from_receiver and not owner and not ctx['teacher']),
                self.object.answers_in_ordered_list()
            ))
        return self.render_to_response(ctx)


####
#
# DELETE VIEWS
#

class OriginalSubmissionDeleteView(IsTeacherMixin, CourseContextMixin, DeleteView):
    model = OriginalSubmission
    pk_url_kwarg = 'sub_pk'

    def get_object(self):
        self.object = None
        ctx = self.get_context_data()
        obj = super().get_object()
        if obj.course != ctx['course']:
            raise PermissionDenied('You cannot remove submissions from other courses...')
        return obj

    def get_success_url(self):
        return reverse_lazy('courses:submissions:original-list', kwargs={
            'base_url_slug': self.kwargs['base_url_slug'],
            'url_slug': self.kwargs['url_slug'],
            'pk': self.kwargs['pk']
            })


class ReviewSubmissionDeleteView(IsTeacherMixin, CourseContextMixin, DeleteView):
    model = ReviewSubmission
    pk_url_kwarg = 'sub_pk'

    def get_object(self):
        self.object = None
        ctx = self.get_context_data()
        obj = super().get_object()
        if obj.course != ctx['course']:
            raise PermissionDenied('You cannot remove submissions from other courses...')
        return obj

    def get_success_url(self):
        return reverse_lazy('courses:submissions:review-list', kwargs={
            'base_url_slug': self.kwargs['base_url_slug'],
            'url_slug': self.kwargs['url_slug'],
            'pk': self.kwargs['pk']
            })


class DownloadSubmissionView(View):

    # TODO: rewrite this whole mess
    def get(self, *args, **kwargs):
        user = self.request.user
        dl_token = self.request.GET.get('dl_token', None)
        if user.is_anonymous and not dl_token:
            raise PermissionDenied

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
            # review_exercise might not exist yet if the teacher has only
            # configured the submission exercise
            if hasattr(obj.exercise, 'review_exercise') and obj.exercise.review_exercise is not None:
                re = obj.exercise.review_exercise
            else:
                re = None
            file_itself = obj.file

        if dl_token:
            if dtype == 'answer':
                subid = obj.submission.pk
            else:
                subid = obj.pk
            if not DownloadToken.objects.filter(submission_id=subid, token=dl_token).exists():
                raise PermissionDenied('There\'s a problem with the download token.')

        else:

            enrolled_can_access = False
            if re and re.type == ReviewExercise.CHOOSE and dtype == 'osub':
                # anyone on the course can download anything
                enrolled_can_access = True

            reviewer = False
            receiver = False
            if dtype == 'osub':
                pks_of_users_reviewables = []
                if re:
                    pks_of_users_reviewables = re.reviewlocks_for(self.request.user) \
                                                 .values_list('original_submission', flat=True)
                reviewer = kwargs['pk'] in pks_of_users_reviewables
            else:
                receiver = obj.submission.reviewed_submission.is_owner(user) and \
                            not obj.question.hide_from_receiver

            if not teacher and not owner and not reviewer and not receiver and not enrolled_can_access:
                raise PermissionDenied

        filename = file_itself.name.split('/')[-1]
        response = HttpResponse(file_itself, content_type='text/plain')
        # TODO: enough headers? meta type etc.?
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        return response


class ReviewSubmissionEmbeddedFeedbackList(LoginRequiredMixin, CourseContextMixin, ListView):
    model = ReviewSubmission
    template_name = "submissions/reviewsubmission_list_embed.html"

    def get_queryset(self):
        re = ReviewExercise.objects.get(pk=self.kwargs['pk'])
        return re.last_reviews_for(self.request.user)

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['exercise'] = ReviewExercise.objects.get(pk=self.kwargs['pk'])

        if ctx['exercise'].reviews_available_date_in_future():
            ctx['reviews_available_date_in_future'] = True
            ctx['object_list'] = ReviewSubmission.objects.none()

        if not ctx['exercise'].review_showing_requirements_ok(self.request.user):
            ctx['needs_to_complete_more_reviews'] = True
            ctx['object_list'] = ReviewSubmission.objects.none()

        ctx['reviews'] = []
        for review in self.object_list:
            data = []

            for ans in review.answers_in_ordered_list():
                if ans.question.hide_from_receiver:
                    continue

                if ans.value_text:
                    data.append({'q': ans.question.question_text, 'a': ans.value_text})
                elif ans.value_choice:
                    # TODO : braindead ???
                    choice = [c[1] for c in ans.question.choices if c[0] == ans.value_choice][0]
                    data.append({'q': ans.question.question_text, 'a': choice})
                else:
                    token = review.get_download_token_for(self.request.user, self.request)
                    data.append({'q': ans.question.question_text,
                                 'f': ans.get_file_download_url() + "&dl_token=" + token})
            ctx['reviews'].append({'qa_list': data})

        return ctx

