from django.urls import path

from . import views

urlpatterns = [
    path("", views.main, name="main"),
    path("list/", views.list_project, name="list_project"),
    path("projects/<slug:slug>/", views.listing_detail, name="listing_detail"),
    path("projects/<slug:slug>/offer/", views.make_offer, name="make_offer"),
    path("projects/<slug:slug>/favorite/", views.toggle_favorite, name="toggle_favorite"),
]
