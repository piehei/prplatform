from django.forms import Form, ModelForm, Textarea, inlineformset_factory, modelformset_factory, ValidationError, ModelChoiceField
from django.views.generic import TemplateView
from django.http import HttpResponse

import csv

from .utils import create_stats
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

        re = ReviewExercise.objects.get(pk=kwargs['pk'])
        ctx['re'] = re

        ctx['orig_subs'] = re.reviewable_exercise \
                             .last_submission_by_submitters() \
                             .order_by('submitter_group', 'submitter_user')

        if not self.request.GET.get('format'):
            stats, headers = create_stats(ctx, pad=True)
            ctx['stats'] = stats
            ctx['stats_headers'] = headers
            return self.render_to_response(ctx)

        else:

            stats, headers = create_stats(ctx, include_textual_answers=True, pad=True)

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="statistics.csv"'

            writer = csv.writer(response, delimiter=";")
            writer.writerow(headers)
            for submitter_pk in stats:

                osr = stats[submitter_pk]

                row = []

                row += [osr['orig_sub'].submitter]

                row += [",".join([x.reviewed_submission.submitter for x in osr['reviews_by'] if x])]

                row += [",".join([x.submitter for x in osr['reviews_for'] if x])]

                row += [round(avg, 2) if avg is not None else "" for avg in osr['numerical_avgs']]

                # 'text_answer_lists' is a list of padded lists
                # -> flatten
                row += [a for alist in osr['text_answer_lists'] for a in alist]

                writer.writerow(row)

            return response
