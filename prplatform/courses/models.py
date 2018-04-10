from django.urls import reverse
from django.db import models

from prplatform.users.models import User


class Course(models.Model):
    name = models.CharField(max_length=100)
    teachers = models.ManyToManyField(User)

    def get_absolute_url(self):
        return reverse('courses:detail', kwargs={'pk': self.pk})
