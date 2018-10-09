from django.forms import Form, ModelForm, Textarea, inlineformset_factory, modelformset_factory, ValidationError, ModelChoiceField

from .models import SubmissionExercise, ReviewExercise
from .question_models import Question


class SubmissionExerciseForm(ModelForm):
    class Meta:
        model = SubmissionExercise
        fields = ['name', 'description', 'opening_time', 'closing_time', 'visible_to_students',
                  'type', 'aplus_course_id', 'aplus_exercise_id', 'use_groups', 'use_states',
                  'accepted_file_types', 'upload_instructions']
        widgets = {
                'description': Textarea(attrs={'cols': 80, 'rows': 5}),
                'upload_instructions': Textarea(attrs={'cols': 80, 'rows': 5})
                }
        help_texts = {
                'opening_time': 'Date and time in format YYYY-MM-DD HH:MM, eg. 2018-09-12 23:59',
                'closing_time': 'Date and time in format YYYY-MM-DD HH:MM, eg. 2018-09-12 23:59',
                'accepted_file_types': 'A comma separated list of file types. Do not include the period character. ' + \
                                       'Valid examples: pdf or pdf,pptx,docx or py,txt',
                'use_groups': 'If enabled, the students submit the answers as a group instead of individuals. The ' + \
                              'teacher has to configure groups from course edit view.<br><b>Do not change this</b> ' + \
                              'after submissions have been made.',
                'use_states': 'If enabled, the submitted answer will not automatically be put into peer-review process. ' + \
                              'Instead, the teacher can have a look at the submission and has to manually change its state ' + \
                              'to enable peer-review. With this option <b>the teacher can give a boomerang and request changes.</b>'
                }

    def clean(self):
        cd = super().clean()
        type = cd.get('type')
        errors = {
            'accepted_file_types': [],
            'aplus_course_id': [],
            'aplus_exercise_id': []
        }

        if type == SubmissionExercise.TEXT:

            # no extra fields chosen
            field = 'accepted_file_types'
            if cd.get(field):
                errors[field].append('This has to be empty for the chosen type')

            field = 'aplus_course_id'
            if cd.get(field):
                errors[field].append('This has to be empty for the chosen type')

            field = 'aplus_exercise_id'
            if cd.get(field):
                errors[field].append('This has to be empty for the chosen type')

        elif type == SubmissionExercise.FILE_UPLOAD:

            # file type is sensible
            field = 'accepted_file_types'
            accepted_types = cd.get(field)

            if not accepted_types:
                errors[field].append('You have to provide accepted file types')

            if len(accepted_types.split()) != 1:
                errors[field].append('Spaces (or any other whitespace) not allowed in file types')

            # no extra fields chosen
            field = 'aplus_course_id'
            if cd.get(field):
                errors[field].append('This has to be empty for the chosen type')

            field = 'aplus_exercise_id'
            if cd.get(field):
                errors[field].append('This has to be empty for the chosen type')

        elif type == SubmissionExercise.APLUS:

            # required fields for aplus type
            field = 'aplus_course_id'
            if not cd.get(field):
                errors[field].append('You have to provide course id in Plus')

            field = 'aplus_exercise_id'
            if not cd.get(field):
                errors[field].append('You have to provide exercise id in Plus')

            # no extra fields
            field = 'accepted_file_types'
            if cd.get(field):
                errors[field].append('This has to be empty for the chosen type')

        # leave out empty error msg lists
        errors = {field: errors[field] for field in errors if errors[field]}
        raise ValidationError(errors)


class ReviewExerciseForm(ModelForm):
    class Meta:
        model = ReviewExercise
        fields = ['name', 'description', 'opening_time', 'closing_time', 'visible_to_students',
                  'model_answer', 'reviewable_exercise', 'type', 'max_reviews_per_student',
                  'max_reviews_per_submission', 'use_groups',
                  ]
        widgets = {
                'description': Textarea(attrs={'cols': 80, 'rows': 5}),
                'model_answer': Textarea(attrs={'cols': 80, 'rows': 5}),
                }
        help_texts = {
                'opening_time': 'Date and time in format YYYY-MM-DD HH:MM, eg. 2018-09-12 23:59',
                'closing_time': 'Date and time in format YYYY-MM-DD HH:MM, eg. 2018-09-12 23:59',
                'use_groups': 'If enabled, the students submit the answers as a group instead of individuals. The ' + \
                              'teacher has to configure groups from course edit view.',
                }

class QuestionForm(ModelForm):
    class Meta:
        model = Question
        fields = ['text']


QuestionModelFormSet = modelformset_factory(Question,
                                            fields=('text',),
                                            can_delete=True,
                                            can_order=True,
                                            min_num=1,
                                            validate_min=True,
                                            max_num=10,
                                            extra=10)

# QuestionFormSet = inlineformset_factory(ReviewExercise, Question,
                                        # fields=('text',),
                                        # can_delete=True,
                                        # can_order=True,
                                        # max_num=10, extra=10)


class ChooceForm(Form):
    """
    If CHOOCE type is used in ReviewExercise, then this form is used
    to offer the student the choices. This form shows student all the
    other students' submissions so the student can chooce who to review.
    """
    choice = ModelChoiceField(queryset=None, label='')

    def __init__(self, *args, **kwargs):
        exercise = kwargs.pop('exercise')
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        # TODO: groups?
        qs = exercise.reviewable_exercise.submissions \
                     .order_by('submitter_user_id') \
                     .distinct('submitter_user_id') \
                     .exclude(
                        id__in=exercise.reviewable_exercise.submissions_by_submitter(user).values('id'))
        self.fields['choice'].queryset = qs
