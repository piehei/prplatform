from django.views.generic import DetailView, CreateView, ListView, TemplateView, UpdateView
from django.urls import reverse, resolve
from django.http import HttpResponseRedirect
from django.forms import Textarea
from django.forms.models import modelform_factory

from .models import SubmissionExercise, ReviewExercise
from .forms import SubmissionExerciseForm, ReviewExerciseForm
from prplatform.courses.views import CourseContextMixin, IsTeacherMixin


###
#
# CREATE VIEWS
#

class ExerciseCreateView(IsTeacherMixin, CourseContextMixin, TemplateView):
    """ TODO:
        This now lets the template to show the teacher multiple
        different exercise form types. Should they all have their
        different CreateViews or should they be included in the same
        view with some toggles?
    """
    # template_name = "exercises/create.html"

    def get(self, *args, **kwargs):
        """ TODO: currently returns only generalForm """

        context = self.get_context_data(**kwargs)

        # submission or review exercise
        if self.request.resolver_match.url_name == "create-submission-exercise":
            context['generalForm'] = SubmissionExerciseForm()
        else:
            context['generalForm'] = ReviewExerciseForm()

        return self.render_to_response(context)

    def post(self, *args, **kwargs):
        """ TODO: error checking """

        # submission or review exercise
        if self.request.resolver_match.url_name == "create-submission-exercise":
            form = SubmissionExerciseForm(self.request.POST)
        else:
            form = ReviewExerciseForm(self.request.POST)

        course = self.get_context_data()['course']

        if form.is_valid():
            # this initializes a new SubmissionExercise or ReviewExercise object
            # depending on the bound form
            # --> after injecting the ForeignKey course it is safe to save
            exer = form.save(commit=False)
            exer.course = course
            exer.save()
            return HttpResponseRedirect(reverse('courses:teacher', kwargs=kwargs))


class SubmissionExerciseCreateView(ExerciseCreateView):
    model = SubmissionExercise
    template_name = "exercises/submissionexercise_create.html"


class ReviewExerciseCreateView(ExerciseCreateView):
    model = ReviewExercise
    template_name = "exercises/reviewexercise_create.html"


###
#
# UPDATE VIEWS
#

class SubmissionExerciseUpdateView(IsTeacherMixin, CourseContextMixin, UpdateView):
    model = SubmissionExercise
    form_class = SubmissionExerciseForm


###
#
# DETAIL VIEWS
#

class SubmissionExerciseDetailView(CourseContextMixin, DetailView):
    model = SubmissionExercise

