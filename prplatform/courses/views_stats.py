from django.forms import Form, ModelForm, Textarea, inlineformset_factory, modelformset_factory, ValidationError, ModelChoiceField
from django.views.generic import TemplateView

from .views import CourseContextMixin, IsTeacherMixin
from prplatform.exercises.models import ReviewExercise


class StatsForm(Form):
    choice = ModelChoiceField(queryset=None, label='')

    def __init__(self, *args, **kwargs):
        course = kwargs.pop('course')
        super().__init__(*args, **kwargs)
        res = course.reviewexercise_exercises.all()
        self.fields['choice'].queryset = res


class CourseStatsView(CourseContextMixin, IsTeacherMixin, TemplateView):
    template_name = "courses/stats.html"

    def get(self, args, **kwargs):
        ctx = self.get_context_data(**kwargs)
        ctx['form'] = StatsForm(course=ctx['course'])

        sid = self.request.GET.get('choice')
        if not sid:
            ctx['form'] = StatsForm(course=ctx['course'])
            return self.render_to_response(ctx)

        sform = StatsForm(self.request.GET, course=ctx['course'])
        ctx['form'] = sform
        if not sform.is_valid():
            return self.render_to_response(ctx)

        re = ReviewExercise.objects.get(pk=sid)
        ctx['re'] = re
        print(re)

        ctx['orig_subs'] = re.reviewable_exercise.submissions.all().order_by('submitter_group', 'submitter_user')

        d = {}
        for index, orig_sub in enumerate(ctx['orig_subs']):
            print(index)
            key = orig_sub.pk
            d[key] = {'os': orig_sub, 'avgs': [], 'reviews': []}

        numeric_questions = re.questions.exclude(choices__len=0)

        # TODO:
        # this is for UI exploration. move as much as possible of the computation to SQL
        if numeric_questions:
            ctx['numeric_questions'] = []
            for nq in numeric_questions:
                ctx['numeric_questions'].append(nq)
                avg_obj = {'q': nq, 'avg': None}
                for os in ctx['orig_subs']:
                    total = 0
                    count = 0
                    for review_sub in os.reviews.all():
                        d[os.pk]['reviews'].append(review_sub)

                        numeric_answer = review_sub.answers.filter(question=nq).first()
                        if numeric_answer:
                            total += int(numeric_answer.value_choice)
                            count += 1

                    if count != 0:
                        avg_obj['avg'] = total/count
                        d[os.pk]['avgs'].append(avg_obj)

        ctx['stats'] = d
        ctx['max_review_count'] = range(1, max([len(x['reviews']) for x in d.values()]) + 1)
        return self.render_to_response(ctx)

