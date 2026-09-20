from django.contrib import admin

from .models import Profile, PendingSignup

admin.site.register(PendingSignup)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "website")
    search_fields = ("user__username", "user__email", "display_name")
