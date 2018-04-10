from django.contrib import admin

from .models import Course


@admin.register(Course)
class CourseModelAdmin(admin.ModelAdmin):
    pass
