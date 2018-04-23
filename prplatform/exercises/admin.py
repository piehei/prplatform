from django.contrib import admin

from .models import BaseExercise, FileUploadExercise

@admin.register(FileUploadExercise)
class FileUploadExerciseModelAdmin(admin.ModelAdmin):
    pass

