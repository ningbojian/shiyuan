from django.urls import path

from Surname import views

app_name = "Surname"
urlpatterns = [
    path("", views.surname_list, name="list"),
    path("index/", views.index, name="index"),
    path("announce/", views.announce, name="announce"),
    path("developer/", views.developer, name="developer"),
    path("information/", views.information, name="information"),
    path("introduction/", views.introduction, name="introduction"),
    path("origins/", views.origins, name="origins"),
    path("figures/", views.figure_list, name="figures"),
    path("figures/<slug:slug>/", views.figure_detail, name="figure_detail"),
    path("science/", views.science, name="science"),
    path("search/", views.search, name="search"),
    path("<slug:slug>/", views.surname_detail, name="detail"),
]
