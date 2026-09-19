from django import forms

from .models import Offer, Project, SellerInquiry


class SellerInquiryForm(forms.ModelForm):
    class Meta:
        model = SellerInquiry
        fields = [
            "project_name",
            "project_type",
            "asking_price",
            "description",
        ]
        labels = {
            "project_name": "Project name",
            "project_type": "What are you listing?",
            "asking_price": "Asking price (USD)",
            "description": "What should a buyer know?",
        }
        widgets = {
            "project_name": forms.TextInput(),
            "project_type": forms.Select(),
            "asking_price": forms.NumberInput(attrs={"min": 1, "step": 1}),
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} field-input".strip()
            field.required = True
        self.fields["project_type"].choices = [("", "Select a type")] + list(
            Project.ListingType.choices
        )

    def clean_asking_price(self):
        price = self.cleaned_data["asking_price"]
        if price < 100:
            raise forms.ValidationError("Set an asking price of at least $100.")
        return price


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ("amount", "message")
        widgets = {
            "amount": forms.NumberInput(attrs={"min": 1, "step": 1}),
            "message": forms.Textarea(attrs={"rows": 4, "maxlength": 1000}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} field-input".strip()

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount < 1:
            raise forms.ValidationError("Your offer must be at least $1.")
        return amount
