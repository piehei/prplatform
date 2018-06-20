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
    object_list = []

    def get_context_data(self):
        exercise = SubmissionExercise.objects.get(pk=self.kwargs['pk'])
        self.object_list = exercise.submissions.all()
        ctx = super().get_context_data(**self.kwargs)
        if not ctx['teacher']:
            self.object_list = self.object_list.filter(submitter=self.request.user)
        ctx['exercise'] = exercise
        ctx['object_list'] = self.object_list
        return ctx

class ReviewSubmissionListView(IsTeacherMixin, CourseContextMixin, ListView):
    model = ReviewSubmission

    def get_context_data(self):
        exercise = ReviewExercise.objects.get(pk=self.kwargs['pk'])
        self.object_list = exercise.submissions.all()
        ctx = super().get_context_data(**self.kwargs)
        if not ctx['teacher']:
            self.object_list = self.object_list.filter(submitter=self.request.uer)
        ctx['exercise'] = exercise
        ctx['object_list'] = self.object_list
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

        return self.render_to_response(context)


class ReviewSubmissionDetailView(IsTeacherMixin, CourseContextMixin, DetailView):
    model = ReviewSubmission
    pk_url_kwargs = "sub_pk"

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

