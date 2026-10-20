from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Customer, PriceItem, Quote

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
    quote = get_object_or_404(Quote.objects.select_related("customer", "material"), pk=pk)
    return render(request, "estimator/quote_detail.html", {"quote": quote, "calc": quote.calculate()})

def quote_create(request):
    customers = Customer.objects.all()
    materials = PriceItem.objects.filter(active=True, category="material")
    if request.method == "POST":
        try:
            customer = get_object_or_404(Customer, pk=int(request.POST["customer"]))
            material_id = request.POST.get("material") or None
            material = get_object_or_404(PriceItem, pk=int(material_id)) if material_id else None
            def dec(key, default="0"):
                return Decimal(request.POST.get(key, default) or default)
            quote = Quote.objects.create(
                customer=customer, title=request.POST.get("title", "").strip() or "محصول بدون عنوان",
                product_type=request.POST.get("product_type", "جعبه بسته‌بندی"),
                quantity=max(1, int(request.POST.get("quantity", "1000"))),
                width_cm=dec("width_cm", "20"), height_cm=dec("height_cm", "15"), depth_cm=dec("depth_cm", "5"),
                material=material, material_grams_per_unit=dec("material_grams_per_unit", "40"),
                waste_percent=dec("waste_percent", "8"), colors=request.POST.get("colors", "چهار رنگ CMYK"),
                print_cost_per_unit=dec("print_cost_per_unit"), plate_cost=dec("plate_cost"),
                postpress_cost_per_unit=dec("postpress_cost_per_unit"), die_cost=dec("die_cost"),
                setup_cost=dec("setup_cost"), transport_cost=dec("transport_cost"), labor_cost=dec("labor_cost"),
                overhead_percent=dec("overhead_percent", "10"), margin_percent=dec("margin_percent", "20"),
                tax_percent=dec("tax_percent", "0"), notes=request.POST.get("notes", ""),
            )
            messages.success(request, "برآورد ذخیره شد.")
            return redirect("quote_detail", pk=quote.pk)
        except (ValueError, InvalidOperation, KeyError):
            messages.error(request, "برخی مقادیر نامعتبر هستند. اعداد و فیلدهای ضروری را بررسی کنید.")
    return render(request, "estimator/quote_form.html", {"customers": customers, "materials": materials})

def price_list(request):
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    items = PriceItem.objects.all()
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
