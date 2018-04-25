from django.forms import ModelForm

from .models import GeneralExercise


class GeneralExerciseForm(ModelForm):
    class Meta:
        model = GeneralExercise
        fields = ['name', 'description', 'file_upload', 'upload_instructions']

