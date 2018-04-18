from django.contrib import admin

from .models import BaseCourse, Course, Enrollment

@admin.register(BaseCourse)
class BaseCourseModelAdmin(admin.ModelAdmin):
    pass

@admin.register(Course)
class CourseModelAdmin(admin.ModelAdmin):
    pass

@admin.register(Enrollment)
class EnrollmentModelAdmin(admin.ModelAdmin):
    pass
