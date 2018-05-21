from django.forms import ModelForm, modelform_factory, Textarea
from .models import OriginalSubmission, Answer


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
        show_text = kwargs.pop('show_text', None)
        show_file_upload = kwargs.pop('show_file_upload', None)
        super(OriginalSubmissionForm, self).__init__(*args, **kwargs)
        if not show_text:
            # self.fields['text'].widget = HiddenInput()
            del self.fields['text']
            self.fields['file'].required = True
        if not show_file_upload:
            # self.fields['text'].widget = HiddenInput()
            del self.fields['file']
            self.fields['text'].required = True


class AnswerForm(ModelForm):

    class Meta:
        model = Answer
        fields = ['value']
        widgets = {
            'value': Textarea(attrs={'cols': 80, 'rows': 5}),
        }


    def __init__(self, *args, **kwargs):
        question_text = kwargs.pop('question_text')
        super(AnswerForm, self).__init__(*args, **kwargs)
        self.fields['value'].label = question_text


