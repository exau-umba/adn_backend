from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_user_profile_photo_url"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="profile_photo_url",
        ),
        migrations.AddField(
            model_name="user",
            name="profile_photo",
            field=models.ImageField(blank=True, null=True, upload_to="profiles/"),
        ),
    ]

