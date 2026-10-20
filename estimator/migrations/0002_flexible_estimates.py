from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


def seed_product_types(apps, schema_editor):
    ProductType = apps.get_model("estimator", "ProductType")
    defaults = [
        ("جعبه بسته‌بندی", True), ("لیبل", False), ("کاتالوگ", False),
        ("بروشور", False), ("ساک دستی", True), ("پاکت", False), ("محصول دیگر", False),
    ]
    for name, requires_depth in defaults:
        ProductType.objects.get_or_create(name=name, defaults={"requires_depth": requires_depth, "active": True})


class Migration(migrations.Migration):
    dependencies = [("estimator", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="ProductType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True, verbose_name="نوع محصول")),
                ("active", models.BooleanField(default=True, verbose_name="فعال")),
                ("requires_depth", models.BooleanField(default=False, verbose_name="نیازمند عمق / عطف")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="ایجاد")),
            ],
            options={"verbose_name": "نوع محصول", "verbose_name_plural": "انواع محصول", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="PriceItemTier",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("minimum_quantity", models.PositiveIntegerField(verbose_name="حداقل مقدار")),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=16, verbose_name="قیمت واحد (تومان)")),
                ("notes", models.CharField(blank=True, max_length=180, verbose_name="یادداشت")),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tiers", to="estimator.priceitem", verbose_name="قلم قیمت")),
            ],
            options={"verbose_name": "پله قیمت", "verbose_name_plural": "پله‌های قیمت", "ordering": ["minimum_quantity"]},
        ),
        migrations.AddConstraint(
            model_name="priceitemtier",
            constraint=models.UniqueConstraint(fields=("item", "minimum_quantity"), name="unique_item_price_tier"),
        ),
        migrations.AddField(
            model_name="quote", name="sheet_quantity",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="تعداد شیت چاپ"),
        ),
        migrations.AddField(
            model_name="quote", name="products_per_sheet",
            field=models.PositiveIntegerField(default=1, verbose_name="تعداد محصول در هر شیت"),
        ),
        migrations.AlterField(
            model_name="quote", name="depth_cm",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name="عمق / عطف (سانتی‌متر)"),
        ),
        migrations.AlterField(
            model_name="quote", name="quantity",
            field=models.PositiveIntegerField(default=1000, verbose_name="تعداد محصول نهایی"),
        ),
        migrations.AlterField(
            model_name="quote", name="print_cost_per_unit",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=14, verbose_name="هزینه چاپ هر واحد / شیت (تومان)"),
        ),
        migrations.CreateModel(
            name="QuoteMaterial",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=180, verbose_name="شرح ماده")),
                ("quantity", models.DecimalField(decimal_places=4, max_digits=16, verbose_name="مقدار مصرف")),
                ("unit", models.CharField(max_length=40, verbose_name="واحد مصرف")),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=16, verbose_name="نرخ ثبت‌شده واحد (تومان)")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("item", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="estimator.priceitem", verbose_name="ماده اولیه")),
                ("quote", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="material_lines", to="estimator.quote")),
            ],
            options={"verbose_name": "ماده مصرفی برآورد", "verbose_name_plural": "مواد مصرفی برآورد"},
        ),
        migrations.CreateModel(
            name="QuoteCostLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=180, verbose_name="شرح هزینه")),
                ("quantity", models.DecimalField(decimal_places=4, default=Decimal("1"), max_digits=16, verbose_name="مقدار")),
                ("unit", models.CharField(default="مورد", max_length=40, verbose_name="واحد")),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=16, verbose_name="نرخ واحد (تومان)")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("quote", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cost_lines", to="estimator.quote")),
            ],
            options={"verbose_name": "ردیف هزینه تولید", "verbose_name_plural": "ردیف‌های هزینه تولید"},
        ),
        migrations.RunPython(seed_product_types, migrations.RunPython.noop),
    ]
