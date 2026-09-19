from django.contrib import admin

from .models import Category, Favorite, Offer, Project, ProjectImage, SellerInquiry



@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "seller",
        "listing_type",
        "price",
        "verified",
        "featured",
        "is_published",
        "created_at",
    )
    list_filter = ("listing_type", "status", "verified", "featured", "is_published")
    search_fields = ("title", "tag", "slug", "seller__username", "seller__email")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")


@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ("project", "sort_order", "alt_text")
    list_filter = ("project__listing_type",)
    search_fields = ("project__title", "alt_text")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "project", "created_at")
    search_fields = ("user__username", "project__title")


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("project", "buyer", "amount", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("project__title", "buyer__username", "buyer__email")


@admin.register(SellerInquiry)
class SellerInquiryAdmin(admin.ModelAdmin):
    list_display = (
        "project_name",
        "seller",
        "project_type",
        "asking_price",
        "reviewed",
        "created_at",
    )
    list_filter = ("project_type", "reviewed")
    search_fields = ("project_name", "seller__username", "seller__email")
    readonly_fields = ("created_at",)
