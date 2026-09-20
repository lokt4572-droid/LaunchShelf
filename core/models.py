from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Project(models.Model):
    class ListingType(models.TextChoices):
        WEBSITE = "website", "Website"
        BOT = "bot", "Telegram bot"
        APP = "app", "App"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        IN_REVIEW = "review", "In review"
        PUBLISHED = "published", "Published"
        SOLD = "sold", "Sold"

    title = models.CharField(max_length=120)
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="projects",
        blank=True,
        null=True,
        help_text="Account that owns this listing.",
    )
    category = models.ForeignKey(
        "Category",
        on_delete=models.SET_NULL,
        related_name="projects",
        blank=True,
        null=True,
    )
    slug = models.SlugField(max_length=140, unique=True)
    listing_type = models.CharField(max_length=20, choices=ListingType.choices)
    tag = models.CharField(max_length=80)
    price = models.PositiveIntegerField(help_text="Asking price in USD")
    metric = models.CharField(max_length=80, help_text="Headline traction, e.g. 2.4k monthly users")
    description = models.TextField()
    preview_name = models.CharField(max_length=80, blank=True)
    preview_tagline = models.CharField(max_length=160, blank=True)
    visual_class = models.CharField(max_length=8, default="v1")
    visual_label = models.CharField(max_length=40)
    verified = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PUBLISHED,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-featured", "-created_at"]
        indexes = [
            models.Index(fields=["seller", "status"], name="project_seller_status_idx"),
            models.Index(fields=["listing_type", "status"], name="project_type_status_idx"),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        base_slug = self.slug or slugify(self.title)
        base_slug = base_slug.strip("-") or "listing"
        slug = base_slug
        counter = 1

        while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("listing_detail", args=[self.slug])

    @property
    def formatted_price(self):
        return f"${self.price:,}"

    @property
    def type_label(self):
        return self.get_listing_type_display().upper()


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True)
    description = models.CharField(max_length=180, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="images")
    image_url = models.URLField()
    alt_text = models.CharField(max_length=140, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["project", "sort_order"], name="unique_project_image_order")
        ]

    def __str__(self):
        return f"Image for {self.project.title}"


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "project"], name="unique_user_favorite")
        ]

    def __str__(self):
        return f"{self.user} saved {self.project}"


class Offer(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        WITHDRAWN = "withdrawn", "Withdrawn"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="offers")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="offers")
    amount = models.PositiveIntegerField(help_text="Offer amount in USD")
    message = models.TextField(max_length=1_000, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["project", "status"], name="offer_project_status_idx")]

    def __str__(self):
        return f"${self.amount:,} offer for {self.project.title}"


class SellerInquiry(models.Model):
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="seller_inquiries",
        blank=True,
        null=True,
    )
    project_name = models.CharField(max_length=160)
    project_type = models.CharField(max_length=20, choices=Project.ListingType.choices)
    asking_price = models.PositiveIntegerField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Seller inquiries"

    def __str__(self):
        seller_name = self.seller.username if self.seller else "legacy seller"
        return f"{self.project_name} ({seller_name})"
