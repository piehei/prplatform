from django import forms
from django.contrib.postgres.forms import SimpleArrayField

from .question_models import Question


class QuestionModelForm(forms.ModelForm):
    choices = SimpleArrayField(
                            SimpleArrayField(forms.CharField(), delimiter="|"),
                            delimiter="\n",
                            widget=forms.Textarea(attrs={'rows': 5}),
                            required=False,
                            label='Choices'
                            )

    class Meta:
        model = Question
        fields = ['question_text', 'hide_from_receiver', 'choices', 'accepted_filetypes']
        help_texts = {
                'hide_from_receiver': ('<b>PLEASE NOTE:</b>: you can hide *ALL* questions/answers from the'
                                       'peer-reviewed student in the "Edit" tab by choosing '
                                       '"Show reviews only to theacher"'),
                'accepted_filetypes': 'Comma-separated list of filetypes. No whitespace.',
                }

    def clean(self):
        cd = super().clean()
        if cd.get('choices', None) and cd.get('accepted_filetypes', None):
            raise forms.ValidationError('You cannot use "choices" and "accepted filetypes" at the same time.')

        return cd

    def clean_choices(self):
        choices = self.cleaned_data['choices']

        if not choices:
            return choices

        if set([len(x) for x in choices]) != {2}:
            raise forms.ValidationError('Choices do not follow the instructions. '
                                        'Each line should be two values separated by the pipe | character.')

        ints = []
        try:
            ints = [int(option[0]) for option in choices]
        except Exception as e:
            print(e)
            raise forms.ValidationError('First value before the delimiter character "|" MUST BE an integer')

        options = [op[1] for op in choices]
        if len(ints) != len(set(ints)) or len(options) != len(set(options)):
            raise forms.ValidationError('Values MUST BE unique')

        return choices

    def clean_accepted_filetypes(self):
        filetypes = self.cleaned_data['accepted_filetypes']

        if filetypes and len(filetypes.split()) != 1:
            raise forms.ValidationError('Spaces (or any other whitespace) not allowed in file types')

        return filetypes
