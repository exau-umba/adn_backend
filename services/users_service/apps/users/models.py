import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.label


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=30, blank=True)
    roles = models.ManyToManyField(Role, related_name="users", blank=True)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.username
