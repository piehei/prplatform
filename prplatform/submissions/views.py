from django.views.generic import DetailView, ListView

from .models import OriginalSubmission

from prplatform.courses.views import CourseContextMixin, IsTeacherMixin

###
#
# LIST VIEWS
#


class SubmissionListView(IsTeacherMixin, CourseContextMixin, ListView):
    model = OriginalSubmission

    def get(self, *args, **kwargs):
        self.object_list = OriginalSubmission.objects.filter(exercise=kwargs['pk'])
        context = super(SubmissionListView, self).get_context_data(**kwargs)
        # context = self.get_context_data(**kwargs)
        print(context)
        return self.render_to_response(context)


class SubmissionDetailView(IsTeacherMixin, DetailView):
    model = OriginalSubmission

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        print(context)
        return self.render_to_response(context)
