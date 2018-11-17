from django.forms import ModelForm, BooleanField, ValidationError
from django.utils import timezone


class DeviationForm(ModelForm):
    """ This is a generic DeviationForm which can be used with both
        Submission and Review exercises to create Submisison and Review
        Exercise Deviations.

        Please note: model = None in class Meta which means that a
        modelform_factory is needed in order to dynamically create a correct
        version of a form.
    """

    class Meta:
        model = None
        fields = ['user', 'group', 'new_deadline']
        labels = {
                'new_deadline': 'New deadline. The prepopulated value in the input field is the original deadline.'
                }
        help_texts = {
                'new_deadline': 'Date and time in format YYYY-MM-DD HH:MM, eg. 2018-09-12 23:59',
                }

    def __init__(self, *args, **kwargs):
        self.exercise = kwargs.pop('exercise')
        super().__init__(*args, **kwargs)

        self.fields['new_deadline'].initial = self.exercise.closing_time

        if self.exercise.use_groups:
            del self.fields['user']
            self.fields['group'].queryset = self.exercise.course.student_groups \
                                                .exclude(
                                pk__in=self.exercise.deviations.values_list('group__pk', flat=True)
                                                )
            self.fields['group'].required = True
        else:
            del self.fields['group']
            self.fields['user'].queryset = self.exercise.course.students \
                                               .exclude(
                                pk__in=self.exercise.deviations.values_list('user__pk', flat=True)
                                                )
            self.fields['user'].required = True

    def clean(self):

        cd = super().clean()
        if cd['new_deadline'] <= self.exercise.closing_time:
            raise ValidationError('New deadline cannot be before original deadline')

        return cd
