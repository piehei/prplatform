from django.contrib import admin

from .models import OriginalSubmission, ReviewSubmission

@admin.register(OriginalSubmission)
class OriginalSubmissionModelAdmin(admin.ModelAdmin):
    pass

@admin.register(ReviewSubmission)
class ReviewSubmissionModelAdmin(admin.ModelAdmin):
    pass
