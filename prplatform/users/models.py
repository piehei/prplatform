from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


class MyUserManager(UserManager):
    def get_by_natural_key(self, email):
        return self.get(email=email)


class User(AbstractUser):

    objects = MyUserManager()

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = models.CharField(_("Name of User"), blank=True, max_length=255)

    def __str__(self):
        return f"{self.username} {self.email}"

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})
