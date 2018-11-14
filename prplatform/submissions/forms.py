from django.forms import ModelForm, modelform_factory, Textarea, ValidationError, FileInput, RadioSelect, BaseFormSet, formset_factory
from .models import OriginalSubmission, Answer
from prplatform.exercises.models import SubmissionExercise
from django import forms


class OriginalSubmissionForm(ModelForm):

    class Meta:
        model = OriginalSubmission
        fields = ['text', 'file']

    def __init__(self, *args, **kwargs):
        """ Depending on the kwargs 'show_text' and 'show_file_upload'
            the form is instrumented to do so. If the SubmissionExercise
            object has not enabled the submission of a said field it will
            be removed from the presented form.
            The other field, that is not removed, will be marked required.
        """
        from django.forms.widgets import HiddenInput
        type = kwargs.pop('type', None)
        filetypes = kwargs.pop('filetypes', None)
        super().__init__(*args, **kwargs)
        if type == SubmissionExercise.FILE_UPLOAD:
            # self.fields['text'].widget = HiddenInput()
            del self.fields['text']
            self.fields['file'].required = True
            self.fields['file'].label = 'Upload your answer here.'
            self.fields['file'].help_text = f'<b>Accepted filetypes are: {filetypes}</b>'
        if type == SubmissionExercise.TEXT:
            # self.fields['text'].widget = HiddenInput()
            del self.fields['file']
            self.fields['text'].required = True
        if type == SubmissionExercise.APLUS:
            # self.fields['text'].widget = HiddenInput()
            del self.fields['file']
            del self.fields['text']

    def clean(self):
        # TODO: This should be done more elegantly. The form now accepts any file but this raises an error.
        cd = super().clean()
        if self.accepted_filetypes:
            filename = cd.get('file').name
            import os
            if os.path.splitext(filename)[1].replace(".", "") not in self.accepted_filetypes.split(","):
                raise ValidationError('Uploaded file is not of accepted type. ' + \
                                      'Accepted filetypes are: ' + self.accepted_filetypes)


class OriginalSubmissionStateForm(ModelForm):

    class Meta:
        model = OriginalSubmission
        fields = ['state']


# TODO: currently UNUSED
class CompleteAnswerForm(forms.Form):

    def __init__(self, *args, **kwargs):
        question_list = kwargs.pop('question_list')
        super().__init__(*args, **kwargs)

        for q in question_list:
            if q.choices:
                fname = f"{q.pk}-choices"
                self.fields[fname] = forms.ChoiceField()
                self.fields[fname].choices = sorted(q.choices, key=lambda c: c[0])
                self.fields[fname].widget = RadioSelect()
                self.fields[fname].label = q.question_text
                self.fields[fname].required = True if q.required else False
            else:
                fname = f"{q.pk}-text"
                self.fields[fname] = forms.CharField()
                self.fields[fname].widget = forms.Textarea(attrs={'cols': 80, 'rows': 5})
                self.fields[fname].label = q.question_text
                self.fields[fname].required = True if q.required else False


# TODO: currently UNUSED
class AnswerForm(forms.Form):
    def __init__(self, *args, **kwargs):
        q = kwargs.pop('question')
        super().__init__(*args, **kwargs)

        if q.choices:
            fname = f"{q.pk}-choices"
            self.fields[fname] = forms.ChoiceField()
            self.fields[fname].choices = sorted(q.choices, key=lambda c: c[0])
            self.fields[fname].widget = RadioSelect()
            self.fields[fname].label = q.question_text
            self.fields[fname].required = True if q.required else False
        else:
            fname = f"{q.pk}-text"
            self.fields[fname] = forms.CharField()
            self.fields[fname].widget = forms.Textarea(attrs={'cols': 80, 'rows': 5})
            self.fields[fname].label = q.question_text
            self.fields[fname].required = True if q.required else False


class AnswerModelForm(ModelForm):

    class Meta:
        model = Answer
        fields = ['question', 'value_text', 'value_choice', 'uploaded_file']  # two of these is removed below
        widgets = {
            'value_text': Textarea(attrs={'cols': 80, 'rows': 3}),
            'value_choice': RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question')
        question_text = question.question_text
        choices = question.choices
        filetypes = question.accepted_filetypes
        required = question.required


        # this is required to retrieve separate answers from the POST
        self.prefix = f"Q-PREFIX-{question.pk}-"

        super().__init__(*args, **kwargs)

        from django.forms.widgets import HiddenInput
        self.initial = {'question': question}
        self.fields['question'].widget = HiddenInput()

        # if this is a question with choices, remove free text field
        # and limit the choices to the teacher chosen choices
        # (by default the QS is all Choice model objects)
        if choices:
            self.fields['value_choice'].label = question_text
            self.fields['value_choice'].choices = sorted(choices, key=lambda c: c[0])
            if required:
                self.fields['value_choice'].required = True
            self.fields.pop('value_text')
            self.fields.pop('uploaded_file')

        elif filetypes:
            self.fields['uploaded_file'].label = question_text
            self.fields['uploaded_file'].help_text = f'<b>Accepted filetypes: {filetypes}</b>'

            if required:
                self.fields['uploaded_file'].required = True
            self.fields.pop('value_text')
            self.fields.pop('value_choice')

        else:
            self.fields['value_text'].label = question_text
            self.fields['value_text'].help_text = '<b>You can make this text area bigger from the bottom-right corner!</b>'
            if required:
                self.fields['value_text'].required = True
            self.fields.pop('value_choice')
            self.fields.pop('uploaded_file')

    def clean_uploaded_file(self, *args, **kwargs):
        file_itself = self.cleaned_data['uploaded_file']
        if file_itself:
            filename = file_itself.name
            filetypes = self.cleaned_data['question'].accepted_filetypes
            import os
            if os.path.splitext(filename)[1].replace(".", "") not in filetypes.split(","):
                raise ValidationError('Uploaded file is not of accepted type. '
                                      'Accepted filetypes are: ' + filetypes)
        return file_itself

