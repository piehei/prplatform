from django.contrib import admin

from .models import SubmissionExercise, ReviewExercise
from .question_models import Question


@admin.register(SubmissionExercise)
class SubmissionExerciseModelAdmin(admin.ModelAdmin):
    pass

@admin.register(ReviewExercise)
class ReviewExerciseModelAdmin(admin.ModelAdmin):
    pass

@admin.register(Question)
class QuestionModelAdmin(admin.ModelAdmin):
    pass

