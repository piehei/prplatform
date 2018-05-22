from django.forms import ModelForm, Textarea, inlineformset_factory, modelformset_factory

from .models import SubmissionExercise, ReviewExercise, Question


class SubmissionExerciseForm(ModelForm):
    class Meta:
        model = SubmissionExercise
        fields = ['name', 'description', 'text', 'file_upload', 'upload_instructions']
        widgets = {
                'description': Textarea(attrs={'cols': 80, 'rows': 5}),
                'upload_instructions': Textarea(attrs={'cols': 80, 'rows': 5})
                }


class ReviewExerciseForm(ModelForm):
    class Meta:
        model = ReviewExercise
        fields = ['name', 'description', 'reviewable_exercise', 'type']
        widgets = {
                'description': Textarea(attrs={'cols': 80, 'rows': 5}),
                }


class QuestionForm(ModelForm):
    class Meta:
        model = Question
        fields = ['text']


QuestionModelFormSet = modelformset_factory(Question,
                                            fields=('text',),
                                            can_delete=True,
                                            can_order=True,
                                            max_num=10,
                                            extra=10)

QuestionFormSet = inlineformset_factory(ReviewExercise, Question,
                                        fields=('text',),
                                        can_delete=True,
                                        can_order=True,
                                        max_num=10, extra=10)
