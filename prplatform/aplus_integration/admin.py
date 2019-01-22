from django.contrib import admin

from .models import AplusAPICallRequest

@admin.register(AplusAPICallRequest)
class AplusAPICallRequestAdmin(admin.ModelAdmin):
    pass
