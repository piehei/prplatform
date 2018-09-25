from django.forms import ModelForm, modelform_factory, Textarea, ValidationError, FileInput
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
        super().__init__(*args, **kwargs)
        if type == SubmissionExercise.FILE_UPLOAD:
            # self.fields['text'].widget = HiddenInput()
            del self.fields['text']
            self.fields['file'].required = True
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
        if self.accepted_file_types:
            filename = cd.get('file').name
            import os
            if os.path.splitext(filename)[1].replace(".", "") not in self.accepted_file_types.split(","):
                raise ValidationError('Uploaded file is not of accepted type. ' + \
                                      'Accepted file types are: ' + self.accepted_file_types)



class OriginalSubmissionStateForm(ModelForm):

    class Meta:
        model = OriginalSubmission
        fields = ['state']


class AnswerForm(ModelForm):

    class Meta:
        model = Answer
        fields = ['value_text', 'value_choice']  # one of these is removed below
        widgets = {
            'value_text': Textarea(attrs={'cols': 80, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        question_text = kwargs.pop('question_text')
        choices = kwargs.pop('question_choices')
        super().__init__(*args, **kwargs)

        # if this is a question with choices, remove free text field
        # and limit the choices to the teacher chosen choices
        # (by default the QS is all Choice model objects)
        if choices:
            self.fields['value_choice'].label = question_text
            self.fields['value_choice'].queryset = choices  # this is necessary
            self.fields.pop('value_text')
        else:
            self.fields['value_text'].label = question_text
            self.fields.pop('value_choice')

