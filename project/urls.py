"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from Surname import api_urls
from Surname import urls as surname_urls
from Surname.sitemaps import FigureSitemap, StaticViewSitemap, SurnameSitemap
from Surname.views import home
from user import urls as user_urls

sitemaps = {
    "static": StaticViewSitemap,
    "surnames": SurnameSitemap,
    "figures": FigureSitemap,
}

urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("surname/", include(surname_urls, namespace="surname")),
    path("api/v1/", include(api_urls, namespace="api")),
    path("user/", include(user_urls, namespace="user")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots",
    ),
]
