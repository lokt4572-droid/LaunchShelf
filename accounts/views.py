import logging
import secrets
from datetime import timedelta

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.models import Project
from .forms import ProfileForm, SignUpForm
from .models import PendingSignup, Profile

logger = logging.getLogger(__name__)


def _new_verification_code():
    return str(secrets.randbelow(900000) + 100000)


def _send_verification_email(pending_signup):
    """
    Send the verification code via Resend's HTTP API.
    Returns True on success, False on failure. Never raises.
    """
    subject = "Your LaunchShelf verification code"
    minutes = settings.VERIFICATION_CODE_TTL // 60

    html = f"""
        <p>Hi {pending_signup.username},</p>
        <p>Your verification code is:</p>
        <p style="font-size:24px;font-weight:bold;letter-spacing:4px;">
            {pending_signup.verification_code}
        </p>
        <p>This code expires in {minutes} minutes.</p>
        <p>If you didn't request this, ignore this email.</p>
    """

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": [pending_signup.email],
                "subject": subject,
                "html": html,
            },
            timeout=10,
        )
    except requests.RequestException:
        logger.exception("Resend request failed for %s", pending_signup.email)
        return False

    if resp.status_code >= 400:
        logger.error(
            "Resend error %s for %s: %s",
            resp.status_code, pending_signup.email, resp.text,
        )
        return False

    return True


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            code = _new_verification_code()
            expires_at = timezone.now() + timedelta(seconds=settings.VERIFICATION_CODE_TTL)

            try:
                pending_signup, _ = PendingSignup.objects.update_or_create(
                    email=form.cleaned_data["email"],
                    defaults={
                        "username": form.cleaned_data["username"],
                        "password_hash": make_password(form.cleaned_data["password1"]),
                        "verification_code": code,
                        "expires_at": expires_at,
                    },
                )
            except IntegrityError:
                form.add_error(
                    "username",
                    "That username is already waiting for verification. Choose another username.",
                )
                return render(request, "accounts/signup.html", {"form": form})

            if not _send_verification_email(pending_signup):
                pending_signup.delete()
                form.add_error(
                    None,
                    "We could not send the verification email. Please try again in a moment.",
                )
                return render(request, "accounts/signup.html", {"form": form})

            request.session["pending_signup_id"] = pending_signup.id
            return redirect("verify_email")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


def email_verification_code(request):
    pending_id = request.session.get("pending_signup_id")
    if not pending_id:
        return redirect("signup")

    pending = get_object_or_404(PendingSignup, id=pending_id)

    if request.method == "POST":
        code = request.POST.get("code", "").strip()

        if pending.expires_at < timezone.now():
            pending.delete()
            request.session.pop("pending_signup_id", None)
            messages.error(request, "Your code has expired. Please sign up again.")
            return redirect("signup")

        if code != pending.verification_code:
            messages.error(request, "That code is incorrect.")
            return render(request, "accounts/verify_email.html", {"pending": pending})

        # Password in PendingSignup.password_hash is already hashed (make_password),
        # so we assign it directly rather than calling set_password().
        user = User.objects.create(
            username=pending.username,
            email=pending.email,
            password=pending.password_hash,
        )
        pending.delete()
        request.session.pop("pending_signup_id", None)

        # Explicitly set the backend so login() never raises.
        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user)
        return redirect("main")

    return render(request, "accounts/verify_email.html", {"pending": pending})


def resend_verification_code(request):
    if request.method != "POST":
        return redirect("verify_email")

    pending_signup_id = request.session.get("pending_signup_id")
    if not pending_signup_id:
        return redirect("signup")

    pending_signup = PendingSignup.objects.filter(id=pending_signup_id).first()
    if pending_signup is None:
        request.session.pop("pending_signup_id", None)
        return redirect("signup")

    pending_signup.verification_code = _new_verification_code()
    pending_signup.expires_at = timezone.now() + timedelta(seconds=settings.VERIFICATION_CODE_TTL)
    pending_signup.save(update_fields=("verification_code", "expires_at"))

    if _send_verification_email(pending_signup):
        messages.success(request, "A new code has been sent to your email.")
    else:
        messages.error(request, "We couldn't send the code. Please try again shortly.")

    return redirect("verify_email")


@login_required
def profile(request):
    profile_obj, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={"display_name": request.user.get_username()},
    )

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile was updated.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile_obj)

    projects = request.user.projects.filter(
        is_published=True,
        status=Project.Status.PUBLISHED,
    )
    pending_projects = request.user.seller_inquiries.filter(reviewed=False)
    portfolio_value = projects.aggregate(total=Sum("price"))["total"] or 0

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "profile": profile_obj,
            "projects": projects,
            "pending_projects": pending_projects,
            "portfolio_value": portfolio_value,
        },
    )