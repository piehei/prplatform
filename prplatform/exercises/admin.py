from django.contrib import admin

from .models import SubmissionExercise, ReviewExercise
from .question_models import Question, QuestionInUse, Choice, ChoiceInUse


@admin.register(SubmissionExercise)
class SubmissionExerciseModelAdmin(admin.ModelAdmin):
    pass

@admin.register(ReviewExercise)
class ReviewExerciseModelAdmin(admin.ModelAdmin):
    pass

@admin.register(Question)
class QuestionModelAdmin(admin.ModelAdmin):
    pass

@admin.register(QuestionInUse)
class QuestionInUseModelAdmin(admin.ModelAdmin):
    pass

@admin.register(Choice)
class ChoiceModelAdmin(admin.ModelAdmin):
    pass

@admin.register(ChoiceInUse)
class ChoiceInUseModelAdmin(admin.ModelAdmin):
    pass

