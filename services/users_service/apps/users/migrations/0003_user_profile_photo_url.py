from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_role_permissions_and_traces"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="profile_photo_url",
            field=models.URLField(blank=True),
        ),
    ]

