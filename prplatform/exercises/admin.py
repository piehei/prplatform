from django.contrib import admin

from .models import GeneralExercise

@admin.register(GeneralExercise)
class GeneralExerciseModelAdmin(admin.ModelAdmin):
    pass
