from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("estimator", "0002_flexible_estimates")]

    operations = [
        migrations.AddField(
            model_name="quote",
            name="sheet_width_cm",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name="عرض شیت چاپ (سانتی‌متر)"),
        ),
        migrations.AddField(
            model_name="quote",
            name="sheet_height_cm",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name="ارتفاع شیت چاپ (سانتی‌متر)"),
        ),
        migrations.AddField(
            model_name="quote",
            name="sheet_margin_cm",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=6, verbose_name="حاشیه امن شیت از هر طرف (سانتی‌متر)"),
        ),
        migrations.AddField(
            model_name="quote",
            name="sheet_gap_cm",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=6, verbose_name="فاصله بین محصولات روی شیت (سانتی‌متر)"),
        ),
        migrations.AddField(
            model_name="quote",
            name="allow_rotation",
            field=models.BooleanField(default=True, verbose_name="چرخش ۹۰ درجه مجاز است"),
        ),
    ]
