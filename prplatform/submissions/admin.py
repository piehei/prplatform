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
    pass
