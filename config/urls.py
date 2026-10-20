from django.contrib import admin
from django.urls import path
from estimator import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.dashboard, name="dashboard"),
    path("quotes/new/", views.quote_create, name="quote_create"),
    path("quotes/", views.quote_list, name="quote_list"),
    path("quotes/<int:pk>/", views.quote_detail, name="quote_detail"),
    path("prices/", views.price_list, name="price_list"),
    path("prices/new/", views.price_create, name="price_create"),
]
