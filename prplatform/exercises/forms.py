from django.forms import ModelForm, Textarea, inlineformset_factory, modelformset_factory, ValidationError

from .models import SubmissionExercise, ReviewExercise, Question


class SubmissionExerciseForm(ModelForm):
    class Meta:
        model = SubmissionExercise
        fields = ['name', 'description', 'text', 'file_upload', 'accepted_file_types', 'upload_instructions']
        widgets = {
                'description': Textarea(attrs={'cols': 80, 'rows': 5}),
                'upload_instructions': Textarea(attrs={'cols': 80, 'rows': 5})
                }
        help_texts = {
                'accepted_file_types': 'A comma separated list of file types. Do not include the period character. ' + \
                                       'Valid examples: pdf or pdf,pptx,docx or py,txt'
                }

    def clean(self):
        cd = super().clean()
        text = cd.get('text')
        file_upload = cd.get('file_upload')
        accepted_types = cd.get('accepted_file_types')

        if not text and not file_upload:
            raise ValidationError('You have to choose either a text submission or file upload')

        if file_upload and not accepted_types:
            raise ValidationError('You have to provide accepted file types')

        if file_upload:
            if len(accepted_types.split()) != 1:
                raise ValidationError('Spaces (or any other whitespace) not allowed in file types')


class ReviewExerciseForm(ModelForm):
    class Meta:
        model = ReviewExercise
        fields = ['name', 'description', 'model_answer', 'reviewable_exercise', 'type', 'review_count']
        widgets = {
                'description': Textarea(attrs={'cols': 80, 'rows': 5}),
                'model_answer': Textarea(attrs={'cols': 80, 'rows': 5}),
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
