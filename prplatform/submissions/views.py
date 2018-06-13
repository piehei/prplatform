from django.views.generic import DetailView, ListView

from .models import OriginalSubmission, ReviewSubmission


from prplatform.courses.views import CourseContextMixin, IsTeacherMixin, IsSubmitterOrTeacherMixin
from prplatform.exercises.models import SubmissionExercise, ReviewExercise

###
#
# LIST VIEWS
#


class OriginalSubmissionListView(IsTeacherMixin, CourseContextMixin, ListView):
    model = OriginalSubmission

    def get(self, *args, **kwargs):
        self.object_list = OriginalSubmission.objects.filter(exercise=kwargs['pk'])
        context = super(OriginalSubmissionListView, self).get_context_data(**kwargs)
        context['exercise'] = SubmissionExercise.objects.get(pk=kwargs['pk'])
        return self.render_to_response(context)


class ReviewSubmissionListView(IsTeacherMixin, CourseContextMixin, ListView):
    model = ReviewSubmission

    def get(self, *args, **kwargs):
        self.object_list = ReviewSubmission.objects.filter(exercise=kwargs['pk'])
        context = super(ReviewSubmissionListView, self).get_context_data(**kwargs)
        context['exercise'] = ReviewExercise.objects.get(pk=kwargs['pk'])
        return self.render_to_response(context)


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

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)
