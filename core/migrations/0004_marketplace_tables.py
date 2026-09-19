from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0003_project_seller"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=60, unique=True)),
                ("slug", models.SlugField(max_length=70, unique=True)),
                ("description", models.CharField(blank=True, max_length=180)),
            ],
            options={"ordering": ["name"], "verbose_name_plural": "categories"},
        ),
        migrations.AddField(
            model_name="project",
            name="category",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="projects", to="core.category"),
        ),
        migrations.AddField(
            model_name="project",
            name="status",
            field=models.CharField(choices=[("draft", "Draft"), ("review", "In review"), ("published", "Published"), ("sold", "Sold")], db_index=True, default="published", max_length=12),
        ),
        migrations.AddField(
            model_name="project",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.CreateModel(
            name="ProjectImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image_url", models.URLField()),
                ("alt_text", models.CharField(blank=True, max_length=140)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="core.project")),
            ],
            options={"ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="Favorite",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="favorited_by", to="core.project")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="favorites", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Offer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.PositiveIntegerField(help_text="Offer amount in USD")),
                ("message", models.TextField(blank=True, max_length=1000)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("accepted", "Accepted"), ("declined", "Declined"), ("withdrawn", "Withdrawn")], db_index=True, default="pending", max_length=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("buyer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="offers", to=settings.AUTH_USER_MODEL)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="offers", to="core.project")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(model_name="projectimage", constraint=models.UniqueConstraint(fields=("project", "sort_order"), name="unique_project_image_order")),
        migrations.AddConstraint(model_name="favorite", constraint=models.UniqueConstraint(fields=("user", "project"), name="unique_user_favorite")),
        migrations.AddIndex(model_name="project", index=models.Index(fields=["seller", "status"], name="project_seller_status_idx")),
        migrations.AddIndex(model_name="project", index=models.Index(fields=["listing_type", "status"], name="project_type_status_idx")),
        migrations.AddIndex(model_name="offer", index=models.Index(fields=["project", "status"], name="offer_project_status_idx")),
    ]
