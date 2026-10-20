from decimal import Decimal
from django.db import migrations, models


def copy_symmetric_margin(apps, schema_editor):
    Quote = apps.get_model("estimator", "Quote")
    for quote in Quote.objects.all().iterator():
        old = quote.sheet_margin_cm
        quote.sheet_margin_left_cm = old
        quote.sheet_margin_right_cm = old
        quote.sheet_margin_top_cm = old
        quote.sheet_margin_bottom_cm = old
        quote.save(update_fields=[
            "sheet_margin_left_cm", "sheet_margin_right_cm",
            "sheet_margin_top_cm", "sheet_margin_bottom_cm",
        ])


class Migration(migrations.Migration):
    dependencies = [("estimator", "0003_sheet_layout")]

    operations = [
        migrations.AddField(
            model_name="quote",
            name="sheet_margin_left_cm",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=6, verbose_name="حاشیه امن چپ شیت (سانتی‌متر)"),
        ),
        migrations.AddField(
            model_name="quote",
            name="sheet_margin_right_cm",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=6, verbose_name="حاشیه امن راست شیت (سانتی‌متر)"),
        ),
        migrations.AddField(
            model_name="quote",
            name="sheet_margin_top_cm",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=6, verbose_name="حاشیه امن بالای شیت (سانتی‌متر)"),
        ),
        migrations.AddField(
            model_name="quote",
            name="sheet_margin_bottom_cm",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=6, verbose_name="حاشیه امن پایین شیت (سانتی‌متر)"),
        ),
        migrations.RunPython(copy_symmetric_margin, migrations.RunPython.noop),
        migrations.RemoveField(model_name="quote", name="sheet_margin_cm"),
    ]
