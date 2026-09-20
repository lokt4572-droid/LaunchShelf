from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import PendingSignup, Profile


class AccountTests(TestCase):
    signup_data = {
        "username": "builder",
        "email": "builder@example.com",
        "password1": "strong-password-123",
        "password2": "strong-password-123",
    }

    def start_signup(self):
        response = self.client.post(reverse("signup"), self.signup_data)
        self.assertRedirects(response, reverse("verify_email"))
        return PendingSignup.objects.get()

    def test_signup_waits_for_verification_before_creating_user(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "builder",
                "email": "builder@example.com",
                "password1": "strong-password-123",
                "password2": "strong-password-123",
            },
        )
        self.assertRedirects(response, reverse("verify_email"))
        self.assertFalse(User.objects.filter(username="builder").exists())
        self.assertEqual(PendingSignup.objects.count(), 1)

    def test_verification_creates_active_user_and_profile(self):
        pending_signup = self.start_signup()
        response = self.client.post(
            reverse("verify_email"),
            {"verification_code": pending_signup.verification_code},
        )

        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(username="builder")
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password("strong-password-123"))
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertFalse(PendingSignup.objects.exists())

    def test_wrong_verification_code_does_not_create_user(self):
        self.start_signup()

        response = self.client.post(
            reverse("verify_email"),
            {"verification_code": "000000"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid verification code")
        self.assertFalse(User.objects.exists())
        self.assertTrue(PendingSignup.objects.exists())

    def test_expired_verification_code_does_not_create_user(self):
        pending_signup = self.start_signup()
        pending_signup.expires_at = timezone.now() - timedelta(minutes=1)
        pending_signup.save(update_fields=("expires_at",))

        response = self.client.post(
            reverse("verify_email"),
            {"verification_code": pending_signup.verification_code},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "expired")
        self.assertFalse(User.objects.exists())
        self.assertTrue(PendingSignup.objects.exists())

    @patch("accounts.views.send_mail", return_value=1)
    def test_resend_replaces_code_and_refreshes_expiration(self, send_mail):
        pending_signup = self.start_signup()
        old_code = pending_signup.verification_code
        send_mail.reset_mock()

        response = self.client.post(reverse("resend_verification_code"))
        pending_signup.refresh_from_db()

        self.assertRedirects(response, reverse("verify_email"))
        self.assertNotEqual(pending_signup.verification_code, old_code)
        self.assertGreater(pending_signup.expires_at, timezone.now())
        send_mail.assert_called_once()

    def test_listing_requires_login(self):
        response = self.client.get(reverse("list_project"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('list_project')}")

    def test_duplicate_pending_username_returns_form_error(self):
        first_response = self.client.post(
            reverse("signup"),
            {
                "username": "builder",
                "email": "first@example.com",
                "password1": "strong-password-123",
                "password2": "strong-password-123",
            },
        )
        self.assertRedirects(first_response, reverse("verify_email"))

        response = self.client.post(
            reverse("signup"),
            {
                "username": "builder",
                "email": "second@example.com",
                "password1": "strong-password-123",
                "password2": "strong-password-123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "waiting for verification")
