from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import PendingSignup, Profile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("That username is already in use.")

        pending_signup = PendingSignup.objects.filter(username=username).first()
        if pending_signup and pending_signup.email != self.cleaned_data.get("email", ""):
            raise forms.ValidationError(
                "That username is waiting for verification. Choose another username."
            )
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("display_name", "bio", "website")
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
        }


class EmailVerificationForm(forms.Form):
    verification_code = forms.CharField(
        required=True,
        max_length=6,
        min_length=6,
        label="Six-digit code",
        widget=forms.TextInput(
            attrs={
                "class": "field-input verification-input",
                "autocomplete": "one-time-code",
                "inputmode": "numeric",
                "pattern": "[0-9]{6}",
                "placeholder": "000000",
                "aria-describedby": "verification-help",
            }
        ),
    )
