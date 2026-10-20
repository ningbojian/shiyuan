from django.urls import path

from Surname import api

app_name = "api"

urlpatterns = [
    path("surnames/", api.surname_list, name="surnames"),
    path("surnames/<slug:slug>/", api.surname_detail, name="surname_detail"),
    path("search/", api.search, name="search"),
    path("figures/", api.figure_list, name="figures"),
    path("meta/", api.meta, name="meta"),
]
