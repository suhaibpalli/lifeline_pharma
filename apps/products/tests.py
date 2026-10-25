from django.test import TestCase
from decimal import Decimal
from django.urls import reverse
from .models import Category, Manufacturer, Product, ProductImage


class MissingProductImageTestCase(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name='Image regression product',
            category=Category.objects.create(name='Regression category'),
            manufacturer=Manufacturer.objects.create(name='Regression manufacturer'),
            mrp_price=Decimal('10.00'), patient_price=Decimal('9.00'),
            pharmacy_price=Decimal('8.00'), description='Test product',
        )
        ProductImage.objects.create(product=self.product, image='', is_primary=True)
        ProductImage.objects.create(product=self.product, image=None)

    def test_empty_primary_image_is_not_returned(self):
        self.assertIsNone(self.product.primary_image)

    def test_prefetched_empty_primary_image_is_not_returned(self):
        product = Product.objects.prefetch_related('images').get(pk=self.product.pk)
        with self.assertNumQueries(0):
            self.assertIsNone(product.primary_image)

    def test_public_pages_render_with_empty_image_rows(self):
        for path in ['/', '/products/', self.product.get_absolute_url()]:
            self.assertEqual(self.client.get(path).status_code, 200)

    def test_prefetched_primary_image_does_not_query_again(self):
        ProductImage.objects.filter(product=self.product).update(is_primary=False)
        image = ProductImage.objects.create(product=self.product, image='products/test.webp', is_primary=True)
        product = Product.objects.prefetch_related('images').get(pk=self.product.pk)
        with self.assertNumQueries(0):
            self.assertEqual(product.primary_image.pk, image.pk)
