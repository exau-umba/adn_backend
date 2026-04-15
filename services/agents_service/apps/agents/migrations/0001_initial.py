from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Agent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("first_name", models.CharField(max_length=100)),
                ("last_name", models.CharField(max_length=100)),
                ("phone", models.CharField(max_length=30)),
                ("city", models.CharField(max_length=120)),
                ("role", models.CharField(max_length=120)),
                ("service_category", models.CharField(max_length=120)),
                ("experience_years", models.PositiveIntegerField(default=0)),
                ("score", models.DecimalField(decimal_places=2, default=0, max_digits=4)),
                ("status", models.CharField(choices=[("ACTIVE", "Actif"), ("SUSPENDED", "Suspendu")], default="ACTIVE", max_length=20)),
                ("has_signed_employer_contract", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="AgentAvailability",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_time", models.BooleanField(default=False)),
                ("part_time", models.BooleanField(default=False)),
                ("lodged", models.BooleanField(default=False)),
                ("non_lodged", models.BooleanField(default=False)),
                (
                    "agent",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="availability", to="agents.agent"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AgentSkill",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("agent", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="skills", to="agents.agent")),
            ],
            options={"unique_together": {("agent", "name")}},
        ),
    ]
