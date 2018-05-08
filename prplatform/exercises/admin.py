from django.contrib import admin

from .models import SubmissionExercise

@admin.register(SubmissionExercise)
class SubmissionExerciseModelAdmin(admin.ModelAdmin):
    pass
