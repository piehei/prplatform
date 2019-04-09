from django.forms import (
        BooleanField,
        Form,
        ModelForm,
        Textarea,
        ValidationError,
        ModelChoiceField,
    )

from .models import (
        ReviewExercise,
        SubmissionExercise,
    )


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
                  'accepted_filetypes',
                  ]
        widgets = {
                'description': Textarea(attrs={'cols': 80, 'rows': 5}),
                }
        help_texts = {
                'opening_time': 'Date and time in format YYYY-MM-DD HH:MM, eg. 2018-09-12 23:59',
                'closing_time': 'Date and time in format YYYY-MM-DD HH:MM, eg. 2018-09-12 23:59',
                'max_submission_count': 'How many times students can submit. The last submission will be used for ' + \
                                        'peer-review. This is useful if students by accident submit unfinished work.',
                'accepted_filetypes': 'A comma separated list of file types. Do not include the period character. ' + \
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
            'accepted_filetypes': [],
            'aplus_course_id': [],
            'aplus_exercise_id': []
        }

        opening = cd.get('opening_time')
        closing = cd.get('closing_time')

        if opening >= closing:
            raise ValidationError('Exercise cannot close before it opens')

        if type == SubmissionExercise.TEXT:

            # no extra fields chosen
            field = 'accepted_filetypes'
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
            field = 'accepted_filetypes'
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
            field = 'accepted_filetypes'
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
                  'reviewable_exercise',
                  'type',
                  'reviewlock_expiry_hours',
                  'can_review_own_submission',
                  'max_submission_count',
                  'max_reviews_per_submission',
                  'min_submission_count',
                  'require_original_submission',
                  'show_reviews_only_to_teacher',
                  'use_groups',
                  ]
        widgets = {
                'description': Textarea(attrs={'cols': 80, 'rows': 5}),
                }
        labels = {
                'type': 'Peer-review target type (who peer-reviews who)',
                }
        help_texts = {
                'opening_time': 'Date and time in format YYYY-MM-DD HH:MM, eg. 2018-09-12 23:59',
                'closing_time': 'Date and time in format YYYY-MM-DD HH:MM, eg. 2018-09-12 23:59',
                'show_reviews_after_date': 'Date and time in format YYYY-MM-DD HH:MM, eg. 2018-09-12 23:59',
                'use_groups': 'If enabled, the students submit the answers as a group instead of individuals. The ' + \
                              'teacher has to configure groups from course edit view.',
                'reviewlock_expiry_hours': """
<strong>This value works *ONLY* with the type RANDOM above.</strong>
<br>
The system will lock a submission to be peer-reviewed for this many hours before giving it to another student.
The default value, 0, means forever which can potentially lead to a situation where a student never completes
the peer-review but the submission is still locked and no one else will peer-review it. Changing this number to eg. 10
makes the system to expire the lock in 10 hours and thus re-locks the submission to be peer-reviewed by another student
after the time has passed.
<br>
<strong>If the students on the course are required</strong> to do the peer-reviews, then the default value of 0 should be fine.
In other cases chaning this value may make it easier to distribute the peer-reviews. This might be especially useful on
mass courses where students are not required to complete the peer-reviews and they're just a small part of the course exercises.
""",
                'can_review_own_submission': ('Students can give peer-reviews to themselves. '
                                              'This cannot be used with the type "Random".'),
                'show_reviews_only_to_teacher': ('This hides all peer-reviews from the person that is being '
                                                 'peer-reviewed.<br><b>PLEASE NOTE:</b> if you configure multiple '
                                                 'questions, you can also individually choose to hide some of them. '
                                                 'This option *OVERRIDES* that and shows nothing to receivers.'
                                                 )
                }

    def __init__(self, *args, **kwargs):
        course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        self.fields['reviewable_exercise'].queryset = SubmissionExercise.objects.filter(course=course)

    def clean(self):
        cd = super().clean()

        opening = cd.get('opening_time')
        closing = cd.get('closing_time')

        if opening >= closing:
            raise ValidationError('Exercise cannot close before it opens')

        exer_type = cd.get('type')
        can_review_own_submission = cd.get('can_review_own_submission', None)
        use_groups = cd.get('use_groups', None)

        expiry_hours = cd.get('reviewlock_expiry_hours', None)

        if exer_type != ReviewExercise.RANDOM and expiry_hours != 0:
            raise ValidationError(
                'Reviewlock expiry hours can ONLY be changed if type is RANDOM. Change it back to 0 (default value).'
            )

        if can_review_own_submission and exer_type not in [ReviewExercise.CHOOSE, ReviewExercise.GROUP]:

            # TODO:
            # due to a django-crispy-forms and bs4 bug we'll give a general error
            raise ValidationError(
                "There was a problem. 'Can review own submission' cannot be used with the type 'Random'"
            )

        if use_groups and exer_type == ReviewExercise.GROUP:
            raise ValidationError('The option "Use groups" cannot be used when students do peer-reviews '
                                  'about their group members (type is GROUP)')


class ChooseForm(Form):
    """
    If choose type is used in ReviewExercise, then this form is used
    to offer the student the choices. This form shows student all the
    other students' submissions so the student can choose who to review.

    If the type of the Review Exercise is "GROUP", then the form
    shows only those in the student's own group.
    """

    choice = ModelChoiceField(queryset=None, label='', empty_label="(Nothing)", required=False)

    def __init__(self, *args, **kwargs):
        exercise = kwargs.pop('exercise')
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        qs = exercise.get_choose_type_queryset(user)

        self.fields['choice'].queryset = qs
        if qs.count() == 0:
            self.fields['choice'].help_text = "<b>Unfortunately no one has returned anything.</b> " + \
                                              "You cannot choose anything just yet."

        self.fields['choice'].label_from_instance = lambda choice: choice.submitter_group if choice.submitter_group else choice.submitter_user
