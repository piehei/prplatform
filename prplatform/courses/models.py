from django.urls import reverse
from django.db import models

from prplatform.core.models import TimeStampedModel
from prplatform.users.models import User


class Course(TimeStampedModel):
    name = models.CharField("Name of the course", max_length=100)
    code = models.CharField("Course code", max_length=50, unique=True)
    url_slug = models.CharField("Identifier that will be used in URL addressses", max_length=50, unique=True)
    school = models.CharField("Name abbreviation of the school, eg. TTY, UTA...", max_length=20)

    teachers = models.ManyToManyField(User)

    def get_absolute_url(self):
        return reverse('courses:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name
