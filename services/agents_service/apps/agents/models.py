import uuid
from django.db import models


class AgentStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Actif"
    SUSPENDED = "SUSPENDED", "Suspendu"


class Agent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    city = models.CharField(max_length=120)
    role = models.CharField(max_length=120)
    service_category = models.CharField(max_length=120)
    experience_years = models.PositiveIntegerField(default=0)
    score = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=AgentStatus.choices, default=AgentStatus.ACTIVE)
    has_signed_employer_contract = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class AgentSkill(models.Model):
    agent = models.ForeignKey(Agent, related_name="skills", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ("agent", "name")


class AgentAvailability(models.Model):
    agent = models.OneToOneField(Agent, related_name="availability", on_delete=models.CASCADE)
    full_time = models.BooleanField(default=False)
    part_time = models.BooleanField(default=False)
    lodged = models.BooleanField(default=False)
    non_lodged = models.BooleanField(default=False)
