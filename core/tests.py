from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Project, SellerInquiry


class MarketplaceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="seller",
            email="seller@example.com",
            password="strong-password-123",
        )
        self.listing = Project.objects.create(
            title="Pulse Metrics",
            slug="pulse-metrics",
            listing_type=Project.ListingType.WEBSITE,
            tag="Analytics SaaS",
            price=4800,
            metric="2.4k monthly users",
            description="A toolkit for focused creators.",
            visual_class="v1",
            visual_label="WEBSITE",
            featured=True,
        )
        Project.objects.create(
            title="Hidden App",
            slug="hidden-app",
            listing_type=Project.ListingType.APP,
            tag="Private",
            price=1000,
            metric="0 users",
            description="Should not appear.",
            visual_class="v3",
            visual_label="MOBILE APP",
            is_published=False,
        )

    def test_home_shows_published_listings_only(self):
        response = self.client.get(reverse("main"))
        self.assertContains(response, "Pulse Metrics")
        self.assertNotContains(response, "Hidden App")
        self.assertContains(response, "1")
        self.assertContains(response, "$4,800")

    def test_listing_detail(self):
        response = self.client.get(self.listing.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A toolkit for focused creators.")

    def test_unpublished_listing_is_404(self):
        response = self.client.get("/projects/hidden-app/")
        self.assertEqual(response.status_code, 404)

    def test_seller_form_rejects_low_price(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("list_project"),
            {
                "project_name": "Tiny Tool",
                "project_type": Project.ListingType.BOT,
                "asking_price": 20,
                "description": "A small bot.",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SellerInquiry.objects.count(), 0)
        self.assertContains(response, "at least $100")

    def test_seller_form_saves_inquiry(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("list_project"),
            {
                "project_name": "Tiny Tool",
                "project_type": Project.ListingType.BOT,
                "asking_price": 500,
                "description": "A small bot with traction.",
            },
        )
        self.assertRedirects(response, reverse("list_project"))
        self.assertEqual(SellerInquiry.objects.count(), 1)
        self.assertEqual(SellerInquiry.objects.get().seller, self.user)

    def test_duplicate_slug_gets_unique_suffix(self):
        Project.objects.create(
            title="Shared Name",
            slug="shared-name",
            listing_type=Project.ListingType.WEBSITE,
            tag="Example",
            price=1000,
            metric="1k users",
            description="First listing.",
            visual_class="v1",
            visual_label="WEBSITE",
        )

        duplicate = Project(
            title="Shared Name",
            listing_type=Project.ListingType.WEBSITE,
            tag="Example",
            price=1200,
            metric="2k users",
            description="Second listing.",
            visual_class="v2",
            visual_label="WEBSITE",
        )
        duplicate.save()

        self.assertEqual(duplicate.slug, "shared-name-1")
