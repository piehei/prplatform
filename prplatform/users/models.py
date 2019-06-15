from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


class MyUserManager(UserManager):
    def get_by_natural_key(self, email):
        return self.get(email=email)


class User(AbstractUser):

    objects = MyUserManager()

    name = models.CharField(_("Name of User"), blank=True, max_length=255)
    temporary = models.BooleanField(default=False)
    lti = models.BooleanField(default=False)

    def __str__(self):
        if self.email.strip() == "":
            return "(no email)"
        if "@" not in self.email:
            return self.email
        return f"{self.email[:self.email.index('@')]}"

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})


class StudentGroup(models.Model):
    name = models.CharField(max_length=30)
    course = models.ForeignKey('courses.Course', related_name='student_groups', on_delete=models.CASCADE)

    # TODO: this field is not utilized anywhere currently
    students = models.ManyToManyField(User, related_name='my_groups')

    student_usernames = ArrayField(models.CharField(max_length=100))

    class Meta:
        unique_together = ['course', 'name']

    def __str__(self):
        return f"{self.name} ({', '.join([x[:x.index('@')] if '@' in x else x for x in self.student_usernames])})"

    def has_student(self, user):
        return user.email in self.student_usernames
