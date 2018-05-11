from django.contrib import admin

from .models import OriginalSubmission

@admin.register(OriginalSubmission)
class OriginalSubmissionModelAdmin(admin.ModelAdmin):
    pass
