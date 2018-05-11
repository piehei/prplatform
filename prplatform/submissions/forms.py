from django.forms import ModelForm
from .models import OriginalSubmission


class OriginalSubmissionForm(ModelForm):

    class Meta:
        model = OriginalSubmission
        fields = ['text', 'file']

    def __init__(self, *args, **kwargs):
        from django.forms.widgets import HiddenInput
        show_text = kwargs.pop('show_text', None)
        show_file_upload = kwargs.pop('show_file_upload', None)
        super(OriginalSubmissionForm, self).__init__(*args, **kwargs)
        if not show_text:
            # self.fields['text'].widget = HiddenInput()
            del self.fields['text']

        if not show_file_upload:
            # self.fields['text'].widget = HiddenInput()
            del self.fields['file']

