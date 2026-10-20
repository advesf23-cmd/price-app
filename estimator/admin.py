from django.contrib import admin
from .models import Customer, PriceItem, Quote

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "created_at")
    search_fields = ("name", "phone", "email")

@admin.register(PriceItem)
class PriceItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "unit", "unit_price", "supplier", "effective_from", "active")
    list_filter = ("category", "active", "effective_from")
    search_fields = ("name", "supplier", "notes")
    list_editable = ("unit_price", "active")

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("title", "customer", "quote_date", "quantity", "status")
    list_filter = ("status", "product_type", "quote_date")
    search_fields = ("title", "customer__name", "notes")
