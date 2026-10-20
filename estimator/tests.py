from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from .models import Customer, Quote, PriceItem, PriceItemTier, ProductType, QuoteCostLine, QuoteMaterial


class QuoteCalculationTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="مشتری تست")

    def test_quote_calculates_basic_totals(self):
        material = PriceItem.objects.create(name="مقوا", category="material", unit="کیلوگرم",
                                            unit_price=Decimal("100000"), active=True)
        quote = Quote.objects.create(customer=self.customer, title="جعبه تست", quantity=100,
            material=material, material_grams_per_unit=Decimal("100"),
            waste_percent=Decimal("0"), print_cost_per_unit=Decimal("100"),
            plate_cost=Decimal("1000"), postpress_cost_per_unit=Decimal("50"),
            overhead_percent=Decimal("0"), margin_percent=Decimal("0"), tax_percent=Decimal("0"))
        result = quote.calculate()
        self.assertEqual(result["material"], Decimal("1000000.00"))
        self.assertEqual(result["printing"], Decimal("11000.00"))
        self.assertEqual(result["postpress"], Decimal("5000.00"))
        self.assertEqual(result["cost"], Decimal("1016000.00"))
        self.assertEqual(result["total"], Decimal("1016000.00"))

    def test_sheet_count_is_used_for_printing_cost(self):
        quote = Quote.objects.create(customer=self.customer, title="لیبل", quantity=1000,
            sheet_quantity=100, products_per_sheet=10, print_cost_per_unit=Decimal("25"),
            overhead_percent=0, margin_percent=0, tax_percent=0)
        self.assertEqual(quote.calculate()["printing"], Decimal("2500.00"))
        self.assertEqual(quote.calculate()["unit"], Decimal("2.50"))

    def test_optional_depth_and_flexible_cost_line(self):
        quote = Quote.objects.create(customer=self.customer, title="لیبل", quantity=10,
            depth_cm=None, overhead_percent=0, margin_percent=0, tax_percent=0)
        QuoteCostLine.objects.create(quote=quote, name="لمینت", quantity=Decimal("2"),
                                     unit="مترمربع", unit_price=Decimal("150"))
        self.assertIsNone(quote.depth_cm)
        self.assertEqual(quote.calculate()["other_costs"], Decimal("300.00"))
        self.assertEqual(quote.calculate()["cost"], Decimal("300.00"))

    def test_tiered_material_rate_is_available(self):
        item = PriceItem.objects.create(name="مقوا", category="material", unit="شیت",
                                        unit_price=Decimal("1000"))
        PriceItemTier.objects.create(item=item, minimum_quantity=100, unit_price=Decimal("800"))
        self.assertEqual(item.tiers.get(minimum_quantity=100).unit_price, Decimal("800"))

    def test_quote_can_be_edited(self):
        quote = Quote.objects.create(customer=self.customer, title="قبل", quantity=100)
        response = self.client.post(reverse("quote_edit", args=[quote.pk]), {
            "customer": self.customer.pk,
            "title": "بعد",
            "product_type": "لیبل",
            "quantity": "200",
            "sheet_quantity": "20",
            "products_per_sheet": "10",
            "width_cm": "10",
            "height_cm": "15",
            "depth_cm": "",
            "material": "",
            "material_grams_per_unit": "0",
            "waste_percent": "0",
            "colors": "چهار رنگ",
            "print_cost_per_unit": "5",
            "plate_cost": "0",
            "postpress_cost_per_unit": "0",
            "die_cost": "0",
            "setup_cost": "0",
            "transport_cost": "0",
            "labor_cost": "0",
            "overhead_percent": "0",
            "margin_percent": "0",
            "tax_percent": "0",
            "status": "draft",
            "notes": "",
            "material_line_item": ["", "", ""],
            "material_line_quantity": ["", "", ""],
            "cost_line_name": ["چاپ خاص", "", ""],
            "cost_line_quantity": ["2", "1", "1"],
            "cost_line_unit": ["متر", "مورد", "مورد"],
            "cost_line_price": ["10", "0", "0"],
        })
        quote.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(quote.title, "بعد")
        self.assertEqual(quote.quantity, 200)
        self.assertEqual(quote.sheet_quantity, 20)
        self.assertEqual(quote.cost_lines.count(), 1)
        self.assertEqual(quote.calculate()["other_costs"], Decimal("20.00"))

    def test_product_type_can_be_managed(self):
        product_type = ProductType.objects.create(name="کیسه اختصاصی", requires_depth=False)
        self.assertTrue(ProductType.objects.filter(name="کیسه اختصاصی", active=True).exists())
        product_type.active = False
        product_type.save()
        self.assertFalse(ProductType.objects.filter(name="کیسه اختصاصی", active=True).exists())
