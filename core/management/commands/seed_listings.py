from django.core.management.base import BaseCommand

from core.models import Project

SEED = [
    {
        "title": "Pulse Metrics",
        "slug": "pulse-metrics",
        "listing_type": Project.ListingType.WEBSITE,
        "tag": "Analytics SaaS",
        "price": 4800,
        "metric": "2.4k monthly users",
        "description": (
            "A lightweight analytics toolkit for independent creators. "
            "Includes a working dashboard, Stripe billing, and a small but loyal user base."
        ),
        "preview_name": "pulsekit.io",
        "preview_tagline": "A toolkit for focused creators.",
        "visual_class": "v1",
        "visual_label": "WEBSITE",
        "featured": True,
    },
    {
        "title": "Recipe Club Bot",
        "slug": "recipe-club-bot",
        "listing_type": Project.ListingType.BOT,
        "tag": "Food & community",
        "price": 1250,
        "metric": "680 active chats",
        "description": (
            "A Telegram bot that shares weekly recipes and keeps food communities active. "
            "Ready to rebrand, with moderation tools and a saved recipe library."
        ),
        "visual_class": "v2",
        "visual_label": "TELEGRAM BOT",
    },
    {
        "title": "Nova Budget",
        "slug": "nova-budget",
        "listing_type": Project.ListingType.APP,
        "tag": "Personal finance",
        "price": 8900,
        "metric": "$430 MRR",
        "description": (
            "A mobile budgeting app with recurring subscriptions and a simple envelope system. "
            "Source, store listings, and current paying users transfer with the sale."
        ),
        "visual_class": "v3",
        "visual_label": "MOBILE APP",
    },
    {
        "title": "Mint Templates",
        "slug": "mint-templates",
        "listing_type": Project.ListingType.WEBSITE,
        "tag": "Ecommerce",
        "price": 2100,
        "metric": "380 sales total",
        "description": (
            "A small template shop with evergreen digital products, Gumroad-style checkout, "
            "and a catalog that already converts."
        ),
        "visual_class": "v4",
        "visual_label": "WEBSITE",
    },
    {
        "title": "Habit Room",
        "slug": "habit-room",
        "listing_type": Project.ListingType.APP,
        "tag": "Wellness",
        "price": 3600,
        "metric": "1.1k downloads",
        "description": (
            "A calm habit tracker for iOS and Android. Includes streak logic, reminders, "
            "and a design system that is easy to extend."
        ),
        "visual_class": "v5",
        "visual_label": "MOBILE APP",
    },
    {
        "title": "Shop Reply AI",
        "slug": "shop-reply-ai",
        "listing_type": Project.ListingType.BOT,
        "tag": "Ecommerce AI",
        "price": 5200,
        "metric": "$620 MRR",
        "description": (
            "A Telegram bot that drafts customer replies for small shops. "
            "Has a prompt library, order-status hooks, and recurring revenue."
        ),
        "visual_class": "v6",
        "visual_label": "TELEGRAM BOT",
    },
]


class Command(BaseCommand):
    help = "Load demo marketplace listings (safe to re-run)."

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for row in SEED:
            _, was_created = Project.objects.update_or_create(
                slug=row["slug"],
                defaults={**row, "verified": True, "is_published": True},
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(
            self.style.SUCCESS(f"Seeded listings: {created} created, {updated} updated.")
        )
