from django.urls import reverse
from django.db import models


class Course(models.Model):
    name = models.CharField(max_length=100)

    def get_absolute_url(self):
        return reverse('courses:detail', kwargs={'pk': self.pk})
