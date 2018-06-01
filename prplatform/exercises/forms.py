from django.forms import ModelForm, Textarea, inlineformset_factory, modelformset_factory, ValidationError

from .models import SubmissionExercise, ReviewExercise, Question


class SubmissionExerciseForm(ModelForm):
    class Meta:
        model = SubmissionExercise
        fields = ['name', 'description', 'type', 'aplus_course_id', 'aplus_exercise_id',
                  'accepted_file_types', 'upload_instructions']
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
        type = cd.get('type')

        if type == SubmissionExercise.FILE_UPLOAD:

            accepted_types = cd.get('accepted_file_types')

            if not accepted_types:
                raise ValidationError('You have to provide accepted file types')

            if len(accepted_types.split()) != 1:
                raise ValidationError('Spaces (or any other whitespace) not allowed in file types')

        elif type == SubmissionExercise.APLUS:

            if not cd.get('aplus_course_id'):
                raise ValidationError('You have to provide course id in Plus')

            if not cd.get('aplus_exercise_id'):
                raise ValidationError('You have to provide exercise id in Plus')

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
