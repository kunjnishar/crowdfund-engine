from django.contrib import admin
from django.urls import include, path

from campaigns.views import index_view

urlpatterns = [
    path("", index_view, name="home"),
    path("admin/", admin.site.urls),
    path("", include("campaigns.urls")),
]