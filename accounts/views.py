from datetime import timedelta
import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from core.models import Project

from .forms import EmailVerificationForm, ProfileForm, SignUpForm
from .models import PendingSignup, Profile


def _new_verification_code():
    return str(secrets.randbelow(900000) + 100000)


def _send_verification_email(pending_signup):
    return send_mail(
        "Email verification",
        f"Your verification code is: {pending_signup.verification_code}",
        settings.EMAIL_HOST_USER,
        [pending_signup.email],
        fail_silently=False,
    )


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

            try:
                sent = _send_verification_email(pending_signup)
            except Exception:
                pending_signup.delete()
                form.add_error(
                    None,
                    "We could not send the verification email. Check your email settings and try again.",
                )
                return render(request, "accounts/signup.html", {"form": form})

            if not sent:
                pending_signup.delete()
                form.add_error(
                    None,
                    "We could not send the verification email. Check your email settings and try again.",
                )
                return render(request, "accounts/signup.html", {"form": form})

            request.session["pending_signup_id"] = pending_signup.id
            return redirect("verify_email")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


@login_required
def profile(request):
    profile, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={"display_name": request.user.get_username()},
    )

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile was updated.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile)

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
            "profile": profile,
            "projects": projects,
            "pending_projects": pending_projects,
            "portfolio_value": portfolio_value,
        },
    )


def email_verification_code(request):
    error = ""
    pending_signup_id = request.session.get("pending_signup_id")

    if not pending_signup_id:
        return redirect("signup")

    if request.method == "POST":
        form = EmailVerificationForm(request.POST)

        if form.is_valid():
            code = form.cleaned_data["verification_code"]

            try:
                pending_signup = PendingSignup.objects.get(
                    id=pending_signup_id,
                    verification_code=code,
                )
            except PendingSignup.DoesNotExist:
                error = "Invalid verification code"
            else:
                if pending_signup.expires_at <= timezone.now():
                    error = "This verification code has expired. Request a new code."
                else:
                    user = User(
                        username=pending_signup.username,
                        email=pending_signup.email,
                        is_active=True,
                    )
                    user.password = pending_signup.password_hash
                    user.save()
                    Profile.objects.create(
                        user=user,
                        display_name=user.get_username(),
                    )
                    pending_signup.delete()
                    del request.session["pending_signup_id"]
                    return redirect("login")
    else:
        form = EmailVerificationForm()

    return render(
        request,
        "accounts/verify_email.html",
        {"form": form, "error": error},
    )


def resend_verification_code(request):
    if request.method != "POST":
        return redirect("verify_email")

    pending_signup_id = request.session.get("pending_signup_id")
    if not pending_signup_id:
        return redirect("signup")

    try:
        pending_signup = PendingSignup.objects.get(id=pending_signup_id)
    except PendingSignup.DoesNotExist:
        request.session.pop("pending_signup_id", None)
        return redirect("signup")

    pending_signup.verification_code = _new_verification_code()
    pending_signup.expires_at = timezone.now() + timedelta(seconds=settings.VERIFICATION_CODE_TTL)
    pending_signup.save(update_fields=("verification_code", "expires_at"))

    try:
        sent = _send_verification_email(pending_signup)
    except Exception:
        sent = False

    if not sent:
        return redirect("verify_email")

    return redirect("verify_email")
