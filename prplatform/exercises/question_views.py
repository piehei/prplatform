from django.views.generic import CreateView, UpdateView, ListView
from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from django.http import HttpResponseRedirect

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
        help_texts = {
                'choices': ''
        }


class QuestionCreateView(IsTeacherMixin, CourseContextMixin, CreateView):
    model = Question
    form = QuestionModelForm
    fields = ['text']
    template_name = "exercises/question_create.html"

    def post(self, *args, **kwargs):
        self.object = None
        course = self.get_context_data()['course']
        form = QuestionModelForm(self.request.POST)
        if form.is_valid():  # and formset.is_valid():
            q = form.save(commit=False)
            q.course = course
            q.save()
            return HttpResponseRedirect(q.get_absolute_url())

        else:
            ctx = self.get_context_data(**kwargs)
            ctx['form'] = form
            return self.render_to_response(ctx)


class CustomQuestionForm(forms.Form):
    text = forms.CharField(max_length=200, required=False)
    previous_choice = forms.ModelMultipleChoiceField(queryset=None, required=False)

    def __init__(self, *args, **kwargs):
        course = kwargs.pop('course')
        super().__init__(*args, **kwargs)
        self.fields['previous_choice'].queryset = course.question_choices.all()


class QuestionUpdateView(IsTeacherMixin, CourseContextMixin, UpdateView):
    model = Question
    fields = ('text', )

    def get_object(self):
        return Question.objects.get(pk=self.kwargs['pk'])

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        ctx = self.get_context_data()
        ctx['form'] = QuestionModelForm(instance=self.get_object())
        cq = CustomQuestionForm(course=ctx['course'])
        ctx['customForm'] = cq

        return self.render_to_response(ctx)

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        form = QuestionModelForm(self.request.POST, instance=self.object)

        if form.is_valid():  # and formset.is_valid():
            q = form.save()
            return HttpResponseRedirect(q.get_absolute_url())
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
