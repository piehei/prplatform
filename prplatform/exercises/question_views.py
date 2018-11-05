from django.views.generic import CreateView, UpdateView, ListView
from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from django.contrib import messages
from django.http import HttpResponseRedirect

from prplatform.exercises.models import ReviewExercise
from prplatform.courses.views import CourseContextMixin, IsTeacherMixin
from .question_models import Question


class QuestionModelForm(forms.ModelForm):
    choices = SimpleArrayField(
                            SimpleArrayField(forms.CharField(), delimiter="|"),
                            delimiter="\n",
                            widget=forms.Textarea(attrs={'rows': 5}),
                            required=False,
                            label='Choices <i>(leave empty if student should answer in text)</i>'
                            )

    class Meta:
        model = Question
        fields = ['text', 'choices']


class QuestionCreateView(IsTeacherMixin, CourseContextMixin, CreateView):
    model = Question
    form = QuestionModelForm
    fields = ('text', 'choices')
    template_name = "exercises/question_create.html"

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data()
        ctx['exercise'] = ReviewExercise.objects.get(pk=self.kwargs['rpk'])
        return ctx

    def get_form(self, *args, **kwargs):
        return QuestionModelForm()

    def post(self, *args, **kwargs):
        self.object = None
        course = self.get_context_data()['course']
        form = QuestionModelForm(self.request.POST)
        if form.is_valid():  # and formset.is_valid():
            q = form.save(commit=False)
            q.course = course
            q.save()
            exercise = ReviewExercise.objects.get(pk=self.kwargs['rpk'])
            exercise.questions.add(q)
            exercise.question_order += [q.pk]
            exercise.save()
            return HttpResponseRedirect(exercise.get_question_url())

        else:
            ctx = self.get_context_data(**kwargs)
            ctx['form'] = form
            return self.render_to_response(ctx)


class QuestionUpdateView(IsTeacherMixin, CourseContextMixin, UpdateView):
    model = Question
    fields = ('text', )

    def get_object(self):
        return Question.objects.get(pk=self.kwargs['pk'])

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        ctx = self.get_context_data()
        ctx['exercise'] = ReviewExercise.objects.get(pk=self.kwargs['rpk'])
        ctx['form'] = QuestionModelForm(instance=self.get_object())

        return self.render_to_response(ctx)

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        form = QuestionModelForm(self.request.POST, instance=self.object)

        if form.is_valid():  # and formset.is_valid():
            q = form.save()
            exercise = ReviewExercise.objects.get(pk=self.kwargs['rpk'])
            messages.success(self.request, 'Question updated successfully')
            return HttpResponseRedirect(exercise.get_question_url())
        else:
            ctx = self.get_context_data(**kwargs)
            ctx['form'] = form
            return self.render_to_response(ctx)


class QuestionDetailView(IsTeacherMixin, CourseContextMixin, UpdateView):
    model = Question
    fields = '__all__'
    template_name = 'exercises/question_detail.html'


class QuestionListView(IsTeacherMixin, CourseContextMixin, ListView):
    model = Question

    def get_context_data(self, *, object_list=None, **kwargs):
        ctx = super().get_context_data()
        ctx['exercise'] = ReviewExercise.objects.get(pk=self.kwargs['pk'])
        ctx['object_list'] = ctx['exercise'].question_list_in_order()

        return ctx

    def post(self, *args, **kwargs):
        """
            This is used to order questions in use in a ReviewExercise.
            The question, identified by pk, can be moved up or down.
            Up from top goes to bottom, down from bottom goes to up.
        """
        self.object_list = None

        direction = self.request.POST.get('dir')
        question_pk = int(self.request.POST.get('question'))
        exer = ReviewExercise.objects.get(pk=self.kwargs['pk'])

        if question_pk in exer.question_order and len(exer.question_order) > 1:

            qorder = exer.question_order
            curr_indx = qorder.index(question_pk)

            if direction == 'up':
                if curr_indx == 0:
                    new_order = qorder[1:] + [question_pk]
                else:
                    new_order = qorder.copy()
                    new_order.insert(curr_indx - 1, new_order.pop(curr_indx))
            else:
                if curr_indx == len(qorder) - 1:
                    new_order = [question_pk] + qorder[:-1]
                else:
                    new_order = qorder.copy()
                    new_order.insert(curr_indx + 1, new_order.pop(curr_indx))

            exer.question_order = new_order
            exer.save()

        return HttpResponseRedirect(exer.get_question_url())
