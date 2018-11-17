from django.forms import ModelForm, BooleanField, ValidationError
from django.utils import timezone

from .deviation_models import SubmissionExerciseDeviation


class DeviationForm(ModelForm):

    class Meta:
        model = SubmissionExerciseDeviation
        fields = ['user', 'group', 'new_deadline']
        help_texts = {
                'new_deadline': 'Date and time in format YYYY-MM-DD HH:MM, eg. 2018-09-12 23:59',
                }
        initial_data = {
                'new_deadline': timezone.now()
                 }

    def __init__(self, *args, **kwargs):
        self.exercise = kwargs.pop('exercise')

        super().__init__(*args, **kwargs)

        if self.exercise.use_groups:
            del self.fields['user']
            self.fields['group'].queryset = self.exercise.course.student_groups.all()
            self.fields['group'].required = True
        else:
            del self.fields['group']
            self.fields['user'].queryset = self.exercise.course.students.all()
            self.fields['user'].required = True

    def clean(self):

        cd = super().clean()
        if cd['new_deadline'] <= self.exercise.closing_time:
            raise ValidationError('New deadline cannot be before original deadline')

        return cd
