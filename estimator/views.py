from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Customer, PriceItem, ProductType, Quote, QuoteMaterial, QuoteCostLine


def dashboard(request):
    recent = Quote.objects.select_related("customer").all()[:8]
    context = {
        "quote_count": Quote.objects.count(),
        "customer_count": Customer.objects.count(),
        "price_count": PriceItem.objects.filter(active=True).count(),
        "recent_quotes": recent,
    }
    return render(request, "estimator/dashboard.html", context)


def quote_list(request):
    q = request.GET.get("q", "").strip()
    quotes = Quote.objects.select_related("customer").all()
    if q:
        quotes = quotes.filter(Q(title__icontains=q) | Q(customer__name__icontains=q) | Q(product_type__icontains=q))
    return render(request, "estimator/quote_list.html", {"quotes": quotes[:250], "q": q})


def quote_detail(request, pk):
    quote = get_object_or_404(
        Quote.objects.select_related("customer", "material").prefetch_related("material_lines", "cost_lines"),
        pk=pk,
    )
    return render(request, "estimator/quote_detail.html", {"quote": quote, "calc": quote.calculate()})


def _decimal(post, key, default="0"):
    raw = post.get(key, default)
    return Decimal(raw if raw not in (None, "") else default)


def _save_quote(request, quote=None):
    """Validate and save a quote while keeping per-quote line prices as snapshots."""
    customer = get_object_or_404(Customer, pk=int(request.POST["customer"]))
    material_id = request.POST.get("material") or None
    material = get_object_or_404(PriceItem, pk=int(material_id), category="material") if material_id else None
    data = {
        "customer": customer,
        "title": request.POST.get("title", "").strip() or "محصول بدون عنوان",
        "product_type": request.POST.get("product_type", "محصول دیگر").strip() or "محصول دیگر",
        "quote_date": request.POST.get("quote_date") or timezone.localdate(),
        "quantity": max(1, int(request.POST.get("quantity", "1000"))),
        "sheet_quantity": int(request.POST["sheet_quantity"]) if request.POST.get("sheet_quantity") else None,
        "products_per_sheet": max(1, int(request.POST.get("products_per_sheet", "1") or "1")),
        "width_cm": _decimal(request.POST, "width_cm", "20"),
        "height_cm": _decimal(request.POST, "height_cm", "15"),
        "depth_cm": _decimal(request.POST, "depth_cm") if request.POST.get("depth_cm") else None,
        "material": material,
        "material_grams_per_unit": _decimal(request.POST, "material_grams_per_unit", "40"),
        "waste_percent": _decimal(request.POST, "waste_percent", "8"),
        "colors": request.POST.get("colors", "چهار رنگ CMYK"),
        "print_cost_per_unit": _decimal(request.POST, "print_cost_per_unit"),
        "plate_cost": _decimal(request.POST, "plate_cost"),
        "postpress_cost_per_unit": _decimal(request.POST, "postpress_cost_per_unit"),
        "die_cost": _decimal(request.POST, "die_cost"),
        "setup_cost": _decimal(request.POST, "setup_cost"),
        "transport_cost": _decimal(request.POST, "transport_cost"),
        "labor_cost": _decimal(request.POST, "labor_cost"),
        "overhead_percent": _decimal(request.POST, "overhead_percent", "10"),
        "margin_percent": _decimal(request.POST, "margin_percent", "20"),
        "tax_percent": _decimal(request.POST, "tax_percent"),
        "status": request.POST.get("status", "draft"),
        "notes": request.POST.get("notes", ""),
    }
    if data["quantity"] < 1 or data["products_per_sheet"] < 1:
        raise ValueError("تعداد باید بیشتر از صفر باشد.")
    if any(data[k] < 0 for k in ("width_cm", "height_cm", "waste_percent", "print_cost_per_unit",
                                    "plate_cost", "postpress_cost_per_unit", "die_cost", "setup_cost",
                                    "transport_cost", "labor_cost", "overhead_percent", "margin_percent", "tax_percent")):
        raise ValueError("مقادیر منفی مجاز نیستند.")
    if quote is None:
        quote = Quote.objects.create(**data)
    else:
        for key, value in data.items():
            setattr(quote, key, value)
        quote.save()

    # Rows are posted as repeated fields, allowing the form to have multiple lines.
    if any(request.POST.getlist("material_line_item")) or any(request.POST.getlist("cost_line_name")):
        quote.material_lines.all().delete()
        quote.cost_lines.all().delete()
        item_ids = request.POST.getlist("material_line_item")
        quantities = request.POST.getlist("material_line_quantity")
        for index, item_id in enumerate(item_ids):
            if not item_id:
                continue
            item = get_object_or_404(PriceItem, pk=int(item_id), category="material", active=True)
            amount = Decimal(quantities[index] or "0") if index < len(quantities) else Decimal("0")
            if amount <= 0:
                continue
            tier = item.tiers.filter(minimum_quantity__lte=amount).order_by("-minimum_quantity").first()
            rate = tier.unit_price if tier else item.unit_price
            QuoteMaterial.objects.create(quote=quote, item=item, name=item.name, quantity=amount,
                                         unit=item.unit, unit_price=rate)
        names = request.POST.getlist("cost_line_name")
        cost_quantities = request.POST.getlist("cost_line_quantity")
        units = request.POST.getlist("cost_line_unit")
        rates = request.POST.getlist("cost_line_price")
        for index, name in enumerate(names):
            name = name.strip()
            if not name:
                continue
            amount = Decimal(cost_quantities[index] or "1") if index < len(cost_quantities) else Decimal("1")
            unit = units[index].strip() if index < len(units) and units[index].strip() else "مورد"
            rate = Decimal(rates[index] or "0") if index < len(rates) else Decimal("0")
            if amount < 0 or rate < 0:
                raise ValueError("مقدار و نرخ ردیف هزینه نمی‌تواند منفی باشد.")
            QuoteCostLine.objects.create(quote=quote, name=name, quantity=amount, unit=unit, unit_price=rate)
    return quote


def _quote_form(request, quote=None):
    customers = Customer.objects.all()
    materials = PriceItem.objects.filter(active=True, category="material").prefetch_related("tiers")
    product_types = ProductType.objects.filter(active=True)
    if request.method == "POST":
        try:
            with transaction.atomic():
                quote = _save_quote(request, quote)
            messages.success(request, "برآورد ذخیره شد.")
            return redirect("quote_detail", pk=quote.pk)
        except (ValueError, InvalidOperation, KeyError, TypeError):
            messages.error(request, "برخی مقادیر نامعتبر هستند. اعداد و فیلدهای ضروری را بررسی کنید.")
    return render(request, "estimator/quote_form.html", {
        "customers": customers, "materials": materials, "product_types": product_types,
        "quote": quote, "is_edit": quote is not None,
        "material_lines": quote.material_lines.all() if quote else [],
        "cost_lines": quote.cost_lines.all() if quote else [],
    })


def quote_create(request):
    return _quote_form(request)


def quote_edit(request, pk):
    quote = get_object_or_404(Quote.objects.select_related("customer", "material"), pk=pk)
    return _quote_form(request, quote)


def price_list(request):
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    items = PriceItem.objects.prefetch_related("tiers").all()
    if q:
        items = items.filter(Q(name__icontains=q) | Q(supplier__icontains=q) | Q(notes__icontains=q))
    if category:
        items = items.filter(category=category)
    return render(request, "estimator/price_list.html", {"items": items[:300], "q": q, "category": category,
        "categories": PriceItem.CATEGORY_CHOICES})


def price_create(request):
    if request.method == "POST":
        try:
            item = PriceItem.objects.create(
                name=request.POST["name"].strip(), category=request.POST["category"],
                unit=request.POST.get("unit", "عدد"), unit_price=Decimal(request.POST["unit_price"]),
                supplier=request.POST.get("supplier", ""), source_url=request.POST.get("source_url", ""),
                notes=request.POST.get("notes", ""), effective_from=request.POST.get("effective_from") or timezone.localdate(),
                active=request.POST.get("active") == "on",
            )
            messages.success(request, "قیمت پایه ذخیره شد.")
            return redirect("price_list")
        except (ValueError, InvalidOperation, KeyError):
            messages.error(request, "اطلاعات قیمت معتبر نیست.")
    return render(request, "estimator/price_form.html", {"categories": PriceItem.CATEGORY_CHOICES})
