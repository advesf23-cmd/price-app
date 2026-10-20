from django.contrib import admin
from .models import Customer, PriceItem, PriceItemTier, ProductType, Quote, QuoteCostLine, QuoteMaterial


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "created_at")
    search_fields = ("name", "phone", "email")


class PriceItemTierInline(admin.TabularInline):
    model = PriceItemTier
    extra = 1


@admin.register(PriceItem)
class PriceItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "unit", "unit_price", "supplier", "effective_from", "active")
    list_filter = ("category", "active", "effective_from")
    search_fields = ("name", "supplier", "notes")
    list_editable = ("unit_price", "active")
    inlines = [PriceItemTierInline]


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "requires_depth", "active")
    list_filter = ("active", "requires_depth")
    search_fields = ("name",)


class QuoteMaterialInline(admin.TabularInline):
    model = QuoteMaterial
    extra = 1


class QuoteCostLineInline(admin.TabularInline):
    model = QuoteCostLine
    extra = 1


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("title", "customer", "quote_date", "quantity", "sheet_quantity", "status")
    list_filter = ("status", "product_type", "quote_date")
    search_fields = ("title", "customer__name", "notes")
    inlines = [QuoteMaterialInline, QuoteCostLineInline]
