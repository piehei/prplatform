from django.views.generic import DetailView, CreateView, UpdateView, ListView
from django import forms
from django.http import HttpResponseRedirect

from prplatform.courses.views import CourseContextMixin, IsTeacherMixin, IsEnrolledMixin
from .models import Question, QuestionChoice


class QuestionModelForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'choices']

QuestionChoicesModelFormSet = forms.modelformset_factory(QuestionChoice,
                                            fields=('text',),
                                            can_delete=True,
                                            can_order=True,
                                            min_num=0,
                                            validate_min=True,
                                            max_num=5,
                                            extra=1)

class QuestionCreateView(IsTeacherMixin, CourseContextMixin, CreateView):
    model = Question
    form = QuestionModelForm
    fields = ['text']
    template_name = "exercises/question_create.html"

    def post(self, *args, **kwargs):
        self.object = None
        course = self.get_context_data()['course']

        form = QuestionModelForm(self.request.POST)
        # formset = QuestionModelFormSet(self.request.POST)

        if form.is_valid(): #and formset.is_valid():

            q = form.save(commit=False)
            q.course = course
            q.save()
            return HttpResponseRedirect(q.get_absolute_url())

        else:
            ctx = self.get_context_data(**kwargs)
            ctx['form'] = form
            ctx['formset'] = formset
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
        ctx['formset'] = QuestionChoicesModelFormSet(queryset=self.object.choices.all())

        cq = CustomQuestionForm(course=ctx['course'])
        # cq.fields['previous_choice'].choices = self.get_choices_for_question(ctx['course'])

        ctx['customForm'] = cq

        return self.render_to_response(ctx)

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        course = self.get_context_data()['course']

        adding_a_choice = self.request.GET.get('choice', None)
        if adding_a_choice:
            print("adding_a_choice")
            cq = CustomQuestionForm(course=course, data=self.request.POST)

            if cq.is_valid():

                print(cq.data)

                if cq.data['text']:
                    print("new text")
                    new_choice = QuestionChoice.objects.create(
                            text=cq.data['text'],
                            course=course,
                            value=0)
                    self.object.choices.add(new_choice)

                elif cq.data['previous_choice']:
                    prev = cq.data['previous_choice']
                    print("connecting old qc")
                    print(prev)

                    # for qcid in cq.data['previous_choice']:
                        # print(qcid)
                    self.object.choices.add(QuestionChoice.objects.get(id=prev))

            print(cq.errors)
            return HttpResponseRedirect(self.object.get_absolute_url())

        form = QuestionModelForm(self.request.POST, instance=self.object)
        # formset = QuestionChoicesModelFormSet(self.request.POST)

        if form.is_valid(): #and formset.is_valid():

            print(form)
            q = form.save(commit=False)
            print(q)
            q.save()
            form.save_m2m()
            # choices = formset.save(commit=False)
            # print(choices)
            # for c in choices:
                # c.value = 0
                # c.save()
                # q.choices.add(c)

            return HttpResponseRedirect(q.get_absolute_url())

        else:
            print(form.errors)
            print(formset.errors)
            ctx = self.get_context_data(**kwargs)
            ctx['form'] = form
            ctx['formset'] = formset
            return self.render_to_response(ctx)

class QuestionDetailView(IsTeacherMixin, CourseContextMixin, UpdateView):
    model = Question
    fields = '__all__'
    template_name = 'exercises/question_detail.html'

class QuestionListView(IsTeacherMixin, CourseContextMixin, ListView):
    model = Question
