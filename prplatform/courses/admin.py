from django.contrib import admin

from .models import BaseCourse, Course

@admin.register(BaseCourse)
class BaseCourseModelAdmin(admin.ModelAdmin):
    pass

@admin.register(Course)
class CourseModelAdmin(admin.ModelAdmin):
    pass
