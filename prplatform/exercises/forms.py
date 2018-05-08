from django.forms import ModelForm

from .models import SubmissionExercise


class SubmissionExerciseForm(ModelForm):
    class Meta:
        model = SubmissionExercise
        fields = ['name', 'description', 'file_upload', 'upload_instructions']

