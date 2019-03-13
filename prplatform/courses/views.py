from django.http import HttpResponseRedirect
from django import forms
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, DetailView, UpdateView, TemplateView
from django.views.generic.edit import ProcessFormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.validators import FileExtensionValidator

from .models import BaseCourse, Course
from prplatform.users.models import StudentGroup
from . import utils


class GroupMixin(object):

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if ctx['object'].use_groups:
            ctx['my_group'] = ctx['course'].find_studentgroup_by_user(self.request.user)
        return ctx


class CourseContextMixin(object):

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['course'] = get_object_or_404(Course, url_slug=self.kwargs['url_slug'],
                                          base_course__url_slug=self.kwargs['base_url_slug'])
        ctx['teacher'] = ctx['course'].is_teacher(self.request.user)
        ctx['enrolled'] = ctx['course'].is_enrolled(self.request.user)
        ctx['reviewable'] = None

        if ctx['course'].hidden and not ctx['teacher']:
            raise PermissionDenied('Only teachers can access this page.')
        return ctx


class ExerciseContextMixin(CourseContextMixin):

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if not self.object.can_access(self.request.user):
            raise PermissionDenied
        return ctx


class IsTeacherMixin(UserPassesTestMixin, LoginRequiredMixin):
    """ This makes sure that the user is logged in and is a teacher
        of the course. 403 forbidden is raised if not. """

    raise_exception = True
    permission_denied_message = "Only teacher of the course can access this page."

    def test_func(self):
        bc = get_object_or_404(BaseCourse, url_slug=self.kwargs['base_url_slug'])
        return bc.is_teacher(self.request.user)


class IsSubmitterMixin(UserPassesTestMixin, LoginRequiredMixin):

    raise_exception = True
    permission_denied_message = "Only the submitter can access this page."

    def test_func(self):
        return self.get_object().submitter == self.request.user


class IsEnrolledMixin(UserPassesTestMixin, LoginRequiredMixin):

    raise_exception = True
    permission_denied_message = "Only enrolled users can access this page. " + \
                                "You can enroll to the course from the course front page."

    def test_func(self):
        course = get_object_or_404(Course, url_slug=self.kwargs['url_slug'],
                                   base_course__url_slug=self.kwargs['base_url_slug'])
        is_enrolled = course.is_enrolled(self.request.user)
        is_teacher = course.is_teacher(self.request.user)
        return is_enrolled or is_teacher


class IsSubmitterOrTeacherMixin(UserPassesTestMixin, LoginRequiredMixin):

    raise_exception = True
    permission_denied_message = "Only the submitter or a teacher can access this page."

    def test_func(self):
        submission = self.get_object()
        is_teacher = get_object_or_404(BaseCourse, url_slug=self.kwargs['base_url_slug']).is_teacher(self.request.user)
        is_submitter = submission.submitter_user == self.request.user
        is_in_group = False
        if submission.submitter_group:
            is_in_group = submission.course.find_studentgroup_by_user(self.request.user) == submission.submitter_group
        return is_submitter or is_teacher or is_in_group


class CourseMixin(object):
    """ This returns the course object itself """

    def get_object(self):
        return get_object_or_404(Course, url_slug=self.kwargs['url_slug'],
                                 base_course__url_slug=self.kwargs['base_url_slug'])


class CourseDetailView(CourseContextMixin, DetailView):
    model = Course
    slug_field = "url_slug"
    slug_url_kwarg = "url_slug"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['submissionexercises'] = self.object.submissionexercise_exercises.all()

        order = self.get_object().exercise_order_on_front_page
        if order:
            print("order")
            # not optimal to sort in python land vs. SQL ***BUT*** the QS is small enough to be just fine
            ctx['submissionexercises'] = sorted(ctx['submissionexercises'],
                                                key=lambda ex: order.index(ex.pk) if ex.pk in order else 100)

        return ctx


class CourseTeacherView(IsTeacherMixin, CourseDetailView):
    template_name = "courses/teacher.html"


class CourseUpdateView(CourseContextMixin, IsTeacherMixin, UpdateView):
    model = Course
    slug_field = "url_slug"
    slug_url_kwarg = "url_slug"
    fields = ['start_date', 'end_date', 'hidden', 'aplus_apikey', 'exercise_order_on_front_page', 'frontpage_info']

    def form_valid(self, form):

        if form.cleaned_data['start_date'] >= form.cleaned_data['end_date']:
            form.errors['end_date'] = ["Course cannot end before it starts"]
            return super().form_invalid(form)

        order = form.cleaned_data['exercise_order_on_front_page']

        if len(order) > 0:
            exercise_pks = self.get_object().submissionexercise_exercises.all().values_list('pk', flat=True)
            minus = set(exercise_pks) - set(order)
            if len(minus) > 0:
                form.errors['exercise_order_on_front_page'] = [(
                        'You have to fill in *ALL* exercise IDs when you'
                        f'define their order on the fron page. You left out: {list(minus)}'
                    )]
                return super().form_invalid(form)

            minus_another_way = set(order) - set(exercise_pks)
            if len(minus_another_way) > 0:
                form.errors['exercise_order_on_front_page'] = [(
                    f'You tried to use an ID that may *NOT* be found from the below list: {list(minus_another_way)}'
                    )]
                return super().form_invalid(form)
        return super().form_valid(form)


class CourseListView(ListView):
    model = Course

    def get_queryset(self, *args, **kwargs):
        obj_list = super().get_queryset()
        visible_ids = [x.pk for x in obj_list if not x.hidden or x.is_teacher(self.request.user)]
        return Course.objects.all().filter(pk__in=visible_ids)


class CourseEnroll(CourseContextMixin, LoginRequiredMixin, ProcessFormView):
    model = Course

    def get_success_url(self):
        return reverse("courses:detail", kwargs={'url_slug': self.kwargs['url_slug'],
                       'base_url_slug': self.kwargs['base_url_slug']})

    def post(self, request, *args, **kwargs):
        course = get_object_or_404(Course,
                                   base_course__url_slug=kwargs['base_url_slug'],
                                   url_slug=kwargs['url_slug'])
        if course.can_enroll(self.request.user):
            course.enroll(self.request.user)
            messages.info(request, "You're now enrolled into the course.")
        else:
            messages.error(request, "You cannot enroll to this course.")
        return HttpResponseRedirect(reverse("courses:detail", kwargs={'url_slug': self.kwargs['url_slug'],
                                    'base_url_slug': self.kwargs['base_url_slug']}))

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse("courses:detail", kwargs={'url_slug': self.kwargs['url_slug'],
                                    'base_url_slug': self.kwargs['base_url_slug']}))


class GroupUploadForm(forms.Form):
    group_file = forms.FileField(label='CSV formatted group file',
                                 validators=[FileExtensionValidator(allowed_extensions=['csv'])])
    moodle_format = forms.BooleanField(required=False, label='CSV is in Moodle format')


class CourseGroupView(CourseContextMixin, IsTeacherMixin, TemplateView):
    model = Course
    template_name = "courses/groups.html"

    def get(self, args, **kwargs):
        ctx = self.get_context_data(**kwargs)
        ctx['form'] = GroupUploadForm(initial={'moodle_format': True})
        ctx['groups'] = StudentGroup.objects.filter(course=ctx['course'])
        return self.render_to_response(ctx)

    @transaction.atomic
    def post(self, args, **kwargs):
        ctx = self.get_context_data(**kwargs)

        form = GroupUploadForm(self.request.POST, self.request.FILES)

        if form.is_valid():
            utils.handle_group_file(self.request, ctx, form)
        else:
            ctx['form'] = form
            ctx['groups'] = StudentGroup.objects.filter(course=ctx['course'])
            return self.render_to_response(ctx)

        return HttpResponseRedirect(reverse("courses:groups", kwargs={'url_slug': self.kwargs['url_slug'],
                                            'base_url_slug': self.kwargs['base_url_slug']}))


class ReviewDealUploadForm(forms.Form):
    dealing_file = forms.FileField(label='CSV formatted review dealing file')


class CourseReviewDealingView(CourseContextMixin, IsTeacherMixin, TemplateView):
    model = Course
    template_name = "courses/dealings.html"

    def get(self, args, **kwargs):
        ctx = self.get_context_data(**kwargs)
        ctx['form'] = ReviewDealUploadForm()
        return self.render_to_response(ctx)

    def post(self, args, **kwargs):
        print("NO OP")
        # ctx = self.get_context_data(**kwargs)
        # group_file = self.request.FILES['group_file']
        # contents = group_file.read().decode('utf-8')
        messages.warning(self.request, "Not implemented yet!")
        return HttpResponseRedirect(reverse("courses:dealings", kwargs={'url_slug': self.kwargs['url_slug'],
                                            'base_url_slug': self.kwargs['base_url_slug']}))

