from django.contrib import admin

from .models import BaseExercise, GeneralExercise

@admin.register(GeneralExercise)
class GeneralExerciseModelAdmin(admin.ModelAdmin):
    pass
