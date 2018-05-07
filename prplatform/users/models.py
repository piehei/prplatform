from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


class UserManager(models.Manager):
    def get_by_natural_key(self, email):
        return self.get(email=email)


class User(AbstractUser):

    objects = UserManager()

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = models.CharField(_("Name of User"), blank=True, max_length=255)

    def __str__(self):
        return self.username + " " + self.name

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})
