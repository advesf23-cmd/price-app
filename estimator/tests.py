from decimal import Decimal
from django.test import TestCase
from .models import Customer, Quote, PriceItem

class QuoteCalculationTests(TestCase):
    def test_quote_calculates_basic_totals(self):
        customer = Customer.objects.create(name="مشتری تست")
        material = PriceItem.objects.create(name="مقوا", category="material", unit="کیلوگرم",
                                            unit_price=Decimal("100000"), active=True)
        quote = Quote.objects.create(customer=customer, title="جعبه تست", quantity=100,
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
