from django.urls import reverse
from django.db import models

from prplatform.core.models import TimeStampedModel
from prplatform.users.models import User


class BaseCourseManager(models.Manager):
    def get_by_natural_key(self, code, school):
        return self.get(code=code, school=school)


class BaseCourse(TimeStampedModel):
    """ This defines a course which the admin will create. The course will have
        a name, code, unique url, school, teachers etc.
        The system will show implementations of this course which will be called
        Courses.
    """
    name = models.CharField("Name of the course", max_length=100)
    code = models.CharField("Course code", max_length=50, unique=True)
    url_slug = models.CharField("Identifier that will be used in URL addressses", max_length=50, unique=True)
    school = models.CharField("Name abbreviation of the school, eg. TTY, UTA...", max_length=20)

    teachers = models.ManyToManyField(User, related_name="base_courses")

    class Meta:
        unique_together = (('code', 'school'))

    def __str__(self):
        return f"{self.name} {self.code} {self.school}"

    def is_teacher(self, user):
        return (user and
                user.is_authenticated and
                (
                    user.is_superuser
                    or
                    (isinstance(user, User) and
                        self.teachers.filter(pk=user.pk).exists()))
                )


class Course(TimeStampedModel):
    """ This is the actual user-facing course which describes an implementation.
    """
    base_course = models.ForeignKey(BaseCourse, on_delete=models.CASCADE, related_name="courses")
    year = models.IntegerField()
    code = models.CharField(max_length=20, blank=True)
    url_slug = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    students = models.ManyToManyField(User, through='Enrollment')

    def get_absolute_url(self):
        return reverse('courses:detail', kwargs={'url_slug': self.url_slug,
                       'base_url_slug': self.base_course.url_slug})

    def __str__(self):
        return f"{self.base_course.code} {self.year} {self.code}"

    def is_enrolled(self, user):
        return (user and
                user.is_authenticated and
                (
                    (isinstance(user, User) and
                        self.students.filter(pk=user.pk).exists()))
                )

    def can_enroll(self, user):
        return (isinstance(user, User) and
                not self.base_course.is_teacher(user) and
                not self.is_enrolled(user)
                )

    def enroll(self, user):
        new_enrollment = Enrollment(student=user, course=self)
        new_enrollment.save()


class Enrollment(TimeStampedModel):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.student) + " -> " + str(self.course)
