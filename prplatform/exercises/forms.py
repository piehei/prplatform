from django.forms import (BooleanField, Form, ModelForm, Textarea, inlineformset_factory, modelformset_factory,
                         ValidationError, ModelChoiceField,)

from .models import SubmissionExercise, ReviewExercise
from .question_models import Question


class SubmissionExerciseForm(ModelForm):
    class Meta:
        model = SubmissionExercise
        fields = ['name',
                  'description',
                  'opening_time',
                  'closing_time',
                  'visible_to_students',
                  'max_submission_count',
                  'type',
                  'aplus_course_id',
                  'aplus_exercise_id',
                  'use_groups',
                  'use_states',
                  'accepted_file_types',
                  ]
        widgets = {
                'description': Textarea(attrs={'cols': 80, 'rows': 5}),
                'upload_instructions': Textarea(attrs={'cols': 80, 'rows': 5})
                }
        help_texts = {
                'opening_time': 'Date and time in format YYYY-MM-DD HH:MM, eg. 2018-09-12 23:59',
                'closing_time': 'Date and time in format YYYY-MM-DD HH:MM, eg. 2018-09-12 23:59',
                'max_submission_count': 'How many times students can submit. The last submission will be used for ' + \
                                        'peer-review. This is useful if students by accident submit unfinished work.',
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

    can_review_own_submission = BooleanField(required=False)

    class Meta:
        model = ReviewExercise
        fields = ['name',
                  'description',
                  'opening_time',
                  'closing_time',
                  'show_reviews_after_date',
                  'visible_to_students',
                  'model_answer',
                  'reviewable_exercise',
                  'type',
                  'can_review_own_submission',
                  'max_reviews_per_student',
                  'max_reviews_per_submission',
                  'minimum_reviews_per_student',
                  'require_original_submission',
                  'use_groups',
                  ]
        widgets = {
                'description': Textarea(attrs={'cols': 80, 'rows': 5}),
                'model_answer': Textarea(attrs={'cols': 80, 'rows': 5}),
                }
        help_texts = {
                'opening_time': 'Date and time in format YYYY-MM-DD HH:MM, eg. 2018-09-12 23:59',
                'closing_time': 'Date and time in format YYYY-MM-DD HH:MM, eg. 2018-09-12 23:59',
                'show_reviews_after_date': 'Date and time in format YYYY-MM-DD HH:MM, eg. 2018-09-12 23:59',
                'use_groups': 'If enabled, the students submit the answers as a group instead of individuals. The ' + \
                              'teacher has to configure groups from course edit view.',
                'can_review_own_submission': 'This is available ONLY for the type "Student chooses"',
                }

    def __init__(self, *args, **kwargs):
        course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        self.fields['reviewable_exercise'].queryset = SubmissionExercise.objects.filter(course=course)

    def clean(self):
        cd = super().clean()

        exer_type = cd.get('type')
        can_review_own_submission = cd.get('can_review_own_submission', None)

        if can_review_own_submission and not exer_type == ReviewExercise.CHOOSE:

            # TODO:
            # due to a django-crispy-forms and bs4 bug we'll give a general error
            raise ValidationError(
                "There was a problem. 'Can review own submission' can *ONLY* be used with the type 'Student chooses'"
            )


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


class ChooseForm(Form):
    """
    If choose type is used in ReviewExercise, then this form is used
    to offer the student the choices. This form shows student all the
    other students' submissions so the student can choose who to review.
    """
    choice = ModelChoiceField(queryset=None, label='')

    def __init__(self, *args, **kwargs):
        exercise = kwargs.pop('exercise')
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        qs = exercise.reviewable_exercise.last_submission_by_submitters()

        if not exercise.can_review_own_submission:
            qs = qs.exclude(
                    id__in=exercise.reviewable_exercise.submissions_by_submitter(user).values('id')
                    )

        if exercise.reviewable_exercise.use_groups:
            qs = qs.order_by('submitter_group__name')
        else:
            qs = qs.order_by('submitter_user__name')

        self.fields['choice'].queryset = qs
