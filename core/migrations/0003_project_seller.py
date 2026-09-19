from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_remove_sellerinquiry_email_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="seller",
            field=models.ForeignKey(
                blank=True,
                help_text="Account that owns this listing.",
                null=True,
                on_delete=models.SET_NULL,
                related_name="projects",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
