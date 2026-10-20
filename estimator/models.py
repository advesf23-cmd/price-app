from decimal import Decimal
from django.db import models
from django.utils import timezone


class Customer(models.Model):
    name = models.CharField("نام مشتری / شرکت", max_length=180)
    phone = models.CharField("تلفن", max_length=40, blank=True)
    email = models.EmailField("ایمیل", blank=True)
    address = models.TextField("نشانی", blank=True)
    notes = models.TextField("یادداشت", blank=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "مشتری"
        verbose_name_plural = "مشتریان"

    def __str__(self):
        return self.name


class ProductType(models.Model):
    name = models.CharField("نوع محصول", max_length=100, unique=True)
    active = models.BooleanField("فعال", default=True)
    requires_depth = models.BooleanField("نیازمند عمق / عطف", default=False)
    created_at = models.DateTimeField("ایجاد", auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "نوع محصول"
        verbose_name_plural = "انواع محصول"

    def __str__(self):
        return self.name


class PriceItem(models.Model):
    CATEGORY_CHOICES = [
        ("material", "مواد اولیه"), ("printing", "چاپ"),
        ("postpress", "خدمات پس از چاپ"), ("logistics", "حمل‌ونقل"),
        ("overhead", "سربار / خدمات دیگر"),
    ]
    name = models.CharField("عنوان قلم هزینه", max_length=180)
    category = models.CharField("دسته", max_length=20, choices=CATEGORY_CHOICES)
    unit = models.CharField("واحد", max_length=40, default="عدد")
    unit_price = models.DecimalField("قیمت واحد (تومان)", max_digits=16, decimal_places=2)
    supplier = models.CharField("تأمین‌کننده / منبع", max_length=180, blank=True)
    effective_from = models.DateField("معتبر از", default=timezone.localdate)
    effective_until = models.DateField("معتبر تا", null=True, blank=True)
    source_url = models.URLField("لینک منبع قیمت", blank=True)
    notes = models.TextField("یادداشت", blank=True)
    active = models.BooleanField("فعال", default=True)
    updated_at = models.DateTimeField("آخرین تغییر", auto_now=True)

    class Meta:
        ordering = ["category", "name"]
        verbose_name = "قیمت پایه"
        verbose_name_plural = "قیمت‌های پایه"

    def __str__(self):
        return f"{self.name} ({self.unit_price} تومان/{self.unit})"


class PriceItemTier(models.Model):
    item = models.ForeignKey(PriceItem, on_delete=models.CASCADE, related_name="tiers", verbose_name="قلم قیمت")
    minimum_quantity = models.PositiveIntegerField("حداقل مقدار")
    unit_price = models.DecimalField("قیمت واحد (تومان)", max_digits=16, decimal_places=2)
    notes = models.CharField("یادداشت", max_length=180, blank=True)

    class Meta:
        ordering = ["minimum_quantity"]
        verbose_name = "پله قیمت"
        verbose_name_plural = "پله‌های قیمت"
        constraints = [models.UniqueConstraint(fields=["item", "minimum_quantity"], name="unique_item_price_tier")]

    def __str__(self):
        return f"{self.item.name}: از {self.minimum_quantity} با نرخ {self.unit_price}"


class Quote(models.Model):
    STATUS_CHOICES = [
        ("draft", "پیش‌نویس"), ("sent", "ارسال‌شده"),
        ("approved", "تأییدشده"), ("rejected", "ردشده"),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, verbose_name="مشتری")
    title = models.CharField("عنوان محصول / پروژه", max_length=200)
    product_type = models.CharField("نوع محصول", max_length=100, default="جعبه بسته‌بندی")
    quote_date = models.DateField("تاریخ برآورد", default=timezone.localdate)
    quantity = models.PositiveIntegerField("تعداد محصول نهایی", default=1000)
    sheet_quantity = models.PositiveIntegerField("تعداد شیت چاپ", null=True, blank=True)
    products_per_sheet = models.PositiveIntegerField("تعداد محصول در هر شیت", default=1)
    width_cm = models.DecimalField("عرض (سانتی‌متر)", max_digits=8, decimal_places=2, default=Decimal("20"))
    height_cm = models.DecimalField("ارتفاع (سانتی‌متر)", max_digits=8, decimal_places=2, default=Decimal("15"))
    depth_cm = models.DecimalField("عمق / عطف (سانتی‌متر)", max_digits=8, decimal_places=2, null=True, blank=True)
    material = models.ForeignKey(PriceItem, on_delete=models.SET_NULL, null=True, blank=True,
                                 limit_choices_to={"category": "material"}, related_name="material_quotes",
                                 verbose_name="ماده اولیه")
    material_grams_per_unit = models.DecimalField("مصرف ماده برای هر محصول (گرم)", max_digits=10, decimal_places=3, default=Decimal("40"))
    waste_percent = models.DecimalField("درصد پرت", max_digits=5, decimal_places=2, default=Decimal("8"))
    colors = models.CharField("مشخصات رنگ", max_length=100, default="چهار رنگ CMYK")
    print_cost_per_unit = models.DecimalField("هزینه چاپ هر واحد / شیت (تومان)", max_digits=14, decimal_places=2, default=Decimal("0"))
    plate_cost = models.DecimalField("هزینه زینک / آماده‌سازی (تومان)", max_digits=14, decimal_places=2, default=Decimal("0"))
    postpress_cost_per_unit = models.DecimalField("خدمات پس از چاپ هر واحد (تومان)", max_digits=14, decimal_places=2, default=Decimal("0"))
    die_cost = models.DecimalField("قالب / تیغ (تومان)", max_digits=14, decimal_places=2, default=Decimal("0"))
    setup_cost = models.DecimalField("آماده‌سازی و تنظیمات (تومان)", max_digits=14, decimal_places=2, default=Decimal("0"))
    transport_cost = models.DecimalField("حمل‌ونقل کل (تومان)", max_digits=14, decimal_places=2, default=Decimal("0"))
    labor_cost = models.DecimalField("دستمزد مستقیم کل (تومان)", max_digits=14, decimal_places=2, default=Decimal("0"))
    overhead_percent = models.DecimalField("درصد سربار", max_digits=5, decimal_places=2, default=Decimal("10"))
    margin_percent = models.DecimalField("حاشیه سود هدف", max_digits=5, decimal_places=2, default=Decimal("20"))
    tax_percent = models.DecimalField("مالیات / عوارض درصدی", max_digits=5, decimal_places=2, default=Decimal("0"))
    status = models.CharField("وضعیت", max_length=12, choices=STATUS_CHOICES, default="draft")
    notes = models.TextField("توضیحات", blank=True)
    created_at = models.DateTimeField("ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین تغییر", auto_now=True)

    class Meta:
        ordering = ["-quote_date", "-id"]
        verbose_name = "برآورد قیمت"
        verbose_name_plural = "برآوردهای قیمت"

    def calculate(self):
        q = Decimal(self.quantity or 0)
        print_quantity = Decimal(self.sheet_quantity if self.sheet_quantity is not None else (self.quantity or 0))
        material_rate = self.material.unit_price if self.material_id else Decimal("0")
        grams = self.material_grams_per_unit * q * (Decimal("1") + self.waste_percent / Decimal("100"))
        if self.material and self.material.unit.lower() in ("کیلوگرم", "kg", "کیلو"):
            material_total = grams / Decimal("1000") * material_rate
        else:
            material_total = q * (Decimal("1") + self.waste_percent / Decimal("100")) * material_rate
        material_lines = sum((line.quantity * line.unit_price for line in self.material_lines.all()), Decimal("0"))
        cost_lines = sum((line.quantity * line.unit_price for line in self.cost_lines.all()), Decimal("0"))
        material_total += material_lines
        printing = print_quantity * self.print_cost_per_unit + self.plate_cost + self.setup_cost
        postpress = q * self.postpress_cost_per_unit + self.die_cost
        direct = material_total + printing + postpress + self.transport_cost + self.labor_cost + cost_lines
        overhead = direct * self.overhead_percent / Decimal("100")
        cost = direct + overhead
        margin = self.margin_percent / Decimal("100")
        sale_before_tax = cost / (Decimal("1") - margin) if margin < Decimal("1") else cost
        tax = sale_before_tax * self.tax_percent / Decimal("100")
        total = sale_before_tax + tax
        return {
            "material": material_total.quantize(Decimal("0.01")),
            "printing": printing.quantize(Decimal("0.01")),
            "postpress": postpress.quantize(Decimal("0.01")),
            "transport": self.transport_cost,
            "labor": self.labor_cost,
            "other_costs": cost_lines.quantize(Decimal("0.01")),
            "direct": direct.quantize(Decimal("0.01")),
            "overhead": overhead.quantize(Decimal("0.01")),
            "cost": cost.quantize(Decimal("0.01")),
            "profit": (sale_before_tax - cost).quantize(Decimal("0.01")),
            "tax": tax.quantize(Decimal("0.01")),
            "total": total.quantize(Decimal("0.01")),
            "unit": (total / q).quantize(Decimal("0.01")) if q else Decimal("0"),
        }

    def __str__(self):
        return f"{self.title} - {self.customer.name}"


class QuoteMaterial(models.Model):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="material_lines")
    item = models.ForeignKey(PriceItem, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="ماده اولیه")
    name = models.CharField("شرح ماده", max_length=180)
    quantity = models.DecimalField("مقدار مصرف", max_digits=16, decimal_places=4)
    unit = models.CharField("واحد مصرف", max_length=40)
    unit_price = models.DecimalField("نرخ ثبت‌شده واحد (تومان)", max_digits=16, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ماده مصرفی برآورد"
        verbose_name_plural = "مواد مصرفی برآورد"

    @property
    def line_total(self):
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))

    @property
    def line_total(self):
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))

    def __str__(self):
        return f"{self.name}: {self.quantity} {self.unit}"


class QuoteCostLine(models.Model):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="cost_lines")
    name = models.CharField("شرح هزینه", max_length=180)
    quantity = models.DecimalField("مقدار", max_digits=16, decimal_places=4, default=Decimal("1"))
    unit = models.CharField("واحد", max_length=40, default="مورد")
    unit_price = models.DecimalField("نرخ واحد (تومان)", max_digits=16, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ردیف هزینه تولید"
        verbose_name_plural = "ردیف‌های هزینه تولید"

    def __str__(self):
        return f"{self.name}: {self.quantity} {self.unit}"
