from datetime import timedelta

from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


def set_existing_expirations(apps, schema_editor):
    pending_signup_model = apps.get_model("accounts", "PendingSignup")
    expiration = timezone.now() + timedelta(seconds=settings.VERIFICATION_CODE_TTL)
    pending_signup_model.objects.filter(expires_at__isnull=True).update(
        expires_at=expiration
    )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_pendingsignup"),
    ]

    operations = [
        migrations.DeleteModel(
            name="EmailVerification",
        ),
        migrations.AlterField(
            model_name="pendingsignup",
            name="verification_code",
            field=models.CharField(max_length=6),
        ),
        migrations.AddField(
            model_name="pendingsignup",
            name="expires_at",
            field=models.DateTimeField(null=True),
        ),
        migrations.RunPython(set_existing_expirations, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="pendingsignup",
            name="expires_at",
            field=models.DateTimeField(),
        ),
    ]