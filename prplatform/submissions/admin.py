from django.contrib import admin

from .models import OriginalSubmission, ReviewSubmission
from .reviewlock_models import ReviewLock

@admin.register(OriginalSubmission)
class OriginalSubmissionModelAdmin(admin.ModelAdmin):
    pass

@admin.register(ReviewSubmission)
class ReviewSubmissionModelAdmin(admin.ModelAdmin):
    pass

@admin.register(ReviewLock)
class ReviewLockModelAdmin(admin.ModelAdmin):
    list_display = ("course", "review_exercise", "created", "original_submission", "user", "group")
    search_fields = ["review_exercise__name", "user__username", "user__email", "user__first_name", "user__last_name", "group__name"]

    def course(self, obj):
        return obj.review_exercise.course
