from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import OfferForm, SellerInquiryForm
from .models import Favorite, Project


def main(request):
    listings = Project.objects.filter(
        is_published=True,
        status=Project.Status.PUBLISHED,
    )
    featured = listings.filter(featured=True).first() or listings.first()
    stats = listings.aggregate(
        listed_count=Count("id"),
        listed_value=Sum("price"),
    )
    listed_value = stats["listed_value"] or 0
    return render(
        request,
        "core/main.html",
        {
            "listings": listings,
            "featured": featured,
            "listed_count": stats["listed_count"] or 0,
            "listed_value": f"{listed_value:,}",
            "type_count": listings.values("listing_type").distinct().count(),
        },
    )


def listing_detail(request, slug):
    listing = get_object_or_404(
        Project,
        slug=slug,
        is_published=True,
        status=Project.Status.PUBLISHED,
    )
    related = (
        Project.objects.filter(
            is_published=True,
            status=Project.Status.PUBLISHED,
            listing_type=listing.listing_type,
        )
        .exclude(pk=listing.pk)[:3]
    )
    is_favorited = request.user.is_authenticated and Favorite.objects.filter(
        user=request.user,
        project=listing,
    ).exists()
    return render(
        request,
        "core/listing_detail.html",
        {
            "listing": listing,
            "related": related,
            "offer_form": OfferForm(),
            "is_favorited": is_favorited,
        },
    )


@login_required
def list_project(request):
    if request.method == "POST":
        form = SellerInquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.seller = request.user
            inquiry.save()
            messages.success(
                request,
                "Thanks — your project is in the review queue. We’ll follow up by email.",
            )
            return redirect("list_project")
    else:
        form = SellerInquiryForm()
    return render(request, "core/list_project.html", {"form": form})


@login_required
def make_offer(request, slug):
    if request.method != "POST":
        return redirect("listing_detail", slug=slug)

    listing = get_object_or_404(
        Project,
        slug=slug,
        is_published=True,
        status=Project.Status.PUBLISHED,
    )
    if listing.seller_id == request.user.id:
        messages.error(request, "You cannot make an offer on your own listing.")
        return redirect("listing_detail", slug=slug)

    form = OfferForm(request.POST)
    if form.is_valid():
        offer = form.save(commit=False)
        offer.project = listing
        offer.buyer = request.user
        offer.save()
        messages.success(request, "Your offer was sent to the seller.")
    else:
        messages.error(request, "Please correct your offer and try again.")
    return redirect("listing_detail", slug=slug)


@login_required
def toggle_favorite(request, slug):
    if request.method != "POST":
        return redirect("listing_detail", slug=slug)

    listing = get_object_or_404(
        Project,
        slug=slug,
        is_published=True,
        status=Project.Status.PUBLISHED,
    )
    favorite, created = Favorite.objects.get_or_create(user=request.user, project=listing)
    if created:
        messages.success(request, "Project saved to your favorites.")
    else:
        favorite.delete()
        messages.success(request, "Project removed from your favorites.")
    return redirect("listing_detail", slug=slug)
