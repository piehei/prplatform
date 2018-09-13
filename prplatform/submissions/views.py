from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import DetailView, ListView

from .models import OriginalSubmission, ReviewSubmission


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
        if not ctx['teacher']:
            self.object_list = self.object_list.filter(submitter=self.request.user)
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
        context = self.get_context_data(**kwargs)

        if self.object.file:
            lines = self.object.file.read().decode("utf-8")
            context['filecontents'] = lines
            print(self.object.file.url)
        return self.render_to_response(context)


class ReviewSubmissionDetailView(IsTeacherMixin, CourseContextMixin, DetailView):
    model = ReviewSubmission
    pk_url_kwargs = "sub_pk"

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class DownloadSubmissionView(View):

    def get(self, *args, **kwargs):
        user = self.request.user

        # user tries to download this
        obj = get_object_or_404(OriginalSubmission, pk=kwargs['pk'])
        print(obj)
        teacher = obj.course.is_teacher(user)
        owner = obj.submitter == user

        pks_of_users_reviewables = user.reviewlock_set.all().values_list('original_submission', flat=True)
        reviewer = kwargs['pk'] in pks_of_users_reviewables

        if not teacher and not owner and not reviewer:
            raise PermissionDenied

        filename = obj.file.name.split('/')[-1]
        response = HttpResponse(obj.file, content_type='text/plain')

        # TODO: enough headers? meta type etc.?
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response
