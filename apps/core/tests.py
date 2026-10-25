from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from apps.core.models import (
    ContactInquiry, DeliveryZone, RetailerEnquiry,
    ProductCatalogue, DoctorVisitRequest
)
from decimal import Decimal
import datetime
from unittest.mock import MagicMock, patch
from django.test import override_settings

class CoreViewsTestCase(TestCase):
    def setUp(self):
        # Set up a delivery zone for testing
        self.zone = DeliveryZone.objects.create(
            name="Chennai Zone 1",
            pincode_start="600001",
            pincode_end="600100",
            delivery_charge=Decimal("40.00"),
            is_serviceable=True,
            estimated_days=2
        )

    def test_home_view(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/home.html')

    def test_about_view(self):
        response = self.client.get(reverse('core:about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/about.html')

    def test_contact_view_get(self):
        response = self.client.get(reverse('core:contact'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/contact.html')

    def test_contact_view_post(self):
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '9876543210',
            'subject': 'General Inquiry',
            'message': 'Hello, I have a query about medicines.'
        }
        response = self.client.post(reverse('core:contact'), data)
        self.assertEqual(response.status_code, 302)  # Redirects to success
        self.assertEqual(ContactInquiry.objects.count(), 1)
        inquiry = ContactInquiry.objects.first()
        self.assertEqual(inquiry.name, 'Test User')
        self.assertEqual(inquiry.subject, 'General Inquiry')

    def test_check_delivery_zone_serviceable(self):
        response = self.client.get(reverse('core:check_delivery') + "?pincode=600092")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['serviceable'])
        self.assertEqual(data['delivery_charge'], 40.00)
        self.assertEqual(data['estimated_days'], 2)
        self.assertEqual(data['zone_name'], 'Chennai Zone 1')

    def test_check_delivery_zone_unserviceable(self):
        response = self.client.get(reverse('core:check_delivery') + "?pincode=999999")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['serviceable'])
        self.assertIn("Sorry, we do not deliver to this pincode yet.", data['message'])

    def test_retailer_enquiry_view_post(self):
        data = {
            'business_name': 'Abc Pharmacy',
            'contact_person': 'Suhaib Palli',
            'email': 'suhaib@pharmacy.com',
            'phone': '9884433074',
            'address': 'No.18 Virugambakkam',
            'city': 'Chennai',
            'state': 'Tamil Nadu',
            'pincode': '600092',
            'gst_number': '33AABCU9603R1ZM',
            'estimated_order_value': '<50k',
            'message': 'Looking for wholesale stocking.'
        }
        response = self.client.post(reverse('core:retailer_enquiry'), data)
        self.assertEqual(response.status_code, 302)  # Redirects to success
        self.assertEqual(RetailerEnquiry.objects.count(), 1)
        enquiry = RetailerEnquiry.objects.first()
        self.assertEqual(enquiry.business_name, 'Abc Pharmacy')
        self.assertEqual(enquiry.phone, '9884433074')

    def test_doctor_visit_request_view_post(self):
        data = {
            'doctor_name': 'Dr. Abijith',
            'specialization': 'General Physician',
            'hospital_name': 'Apollo Hospital',
            'email': 'abijith.apollo@gmail.com',
            'phone': '9876543210',
            'address': 'Greams Road',
            'city': 'Chennai',
            'state': 'Tamil Nadu',
            'preferred_date': (datetime.date.today() + datetime.timedelta(days=7)).strftime('%Y-%m-%d'),
            'preferred_time': 'Morning',
            'purpose': 'Consultation review',
            'notes': 'Looking forward.'
        }
        response = self.client.post(reverse('core:doctor_visit_request'), data)
        self.assertEqual(response.status_code, 302)  # Redirects to success
        self.assertEqual(DoctorVisitRequest.objects.count(), 1)
        req = DoctorVisitRequest.objects.first()
        self.assertEqual(req.doctor_name, 'Dr. Abijith')
        self.assertEqual(req.specialization, 'General Physician')

    def test_pharmacies_view(self):
        response = self.client.get(reverse('core:pharmacies'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/pharmacies.html')

    def test_subscribe_newsletter(self):
        data = {'email': 'newsletter@test.com'}
        response = self.client.post(reverse('core:subscribe_newsletter'), data)
        self.assertEqual(response.status_code, 302)  # Redirects back to referer
        self.assertEqual(ContactInquiry.objects.count(), 1)
        sub = ContactInquiry.objects.first()
        self.assertEqual(sub.email, 'newsletter@test.com')
        self.assertEqual(sub.subject, 'Newsletter Subscription')


class ReadinessTestCase(TestCase):
    def test_invalid_admin_csrf_shows_safe_retry_page(self):
        from django.test import Client

        client = Client(enforce_csrf_checks=True)
        response = client.post('/admin/login/', {'username': 'someone@example.com', 'password': 'invalid'})
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Your sign-in page has expired', status_code=403)
        self.assertNotContains(response, 'DEBUG', status_code=403)
        self.assertNotContains(response, 'CSRF cookie', status_code=403)
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_admin_login_includes_csrf_refresh_and_no_cache(self):
        response = self.client.get('/admin/login/')
        self.assertContains(response, 'js/csrf-form.js')
        self.assertIn('no-store', response['Cache-Control'])

    def test_ready_dependencies_return_no_store_without_session(self):
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok', 'db': 'ok', 'cache': 'ok'})
        self.assertEqual(response['Cache-Control'], 'no-store')
        self.assertNotIn('sessionid', response.cookies)

    @patch('django.db.connection.cursor', side_effect=RuntimeError('secret-connection-string'))
    def test_database_failure_is_unavailable_without_disclosing_details(self, cursor):
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['db'], 'unavailable')
        self.assertNotContains(response, 'secret-connection-string', status_code=503)

    @patch('django.core.cache.cache.get', return_value=None)
    def test_silently_ignored_cache_failure_is_not_healthy(self, cache_get):
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['cache'], 'unavailable')

    @override_settings(HEALTHCHECK_STORAGE=True, MINIO_ENDPOINT_URL='http://127.0.0.1:9000')
    @patch('urllib.request.build_opener')
    def test_storage_failure_degrades_readiness(self, opener):
        opener.return_value.open.side_effect = OSError('private-storage-credentials')
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['storage'], 'unavailable')
        self.assertNotContains(response, 'private-storage-credentials', status_code=503)

    @override_settings(HEALTHCHECK_STORAGE=True, MINIO_ENDPOINT_URL='http://127.0.0.1:9000')
    @patch('urllib.request.build_opener')
    def test_ready_storage_is_included(self, opener):
        opener.return_value.open.return_value.__enter__.return_value.status = 200
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['storage'], 'ok')

    def test_storefront_browsing_does_not_create_guest_carts_or_sessions(self):
        from apps.cart.models import Cart
        from django.contrib.sessions.models import Session

        for path in ['/', '/products/', '/about/']:
            self.assertEqual(self.client.get(path).status_code, 200)
        self.assertEqual(Cart.objects.count(), 0)
        self.assertEqual(Session.objects.count(), 0)


class UploadSafetyTestCase(TestCase):
    def test_image_conversion_preserves_valid_upload(self):
        from io import BytesIO
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .images import convert_to_webp

        output = BytesIO()
        Image.new('RGB', (32, 24), 'white').save(output, format='PNG')
        result = convert_to_webp(SimpleUploadedFile('test.png', output.getvalue()))
        self.assertEqual(result[0], 'test.webp')
        with Image.open(result[1]) as image:
            self.assertEqual(image.size, (32, 24))
            self.assertEqual(image.format, 'WEBP')

    @patch('apps.core.images.Image.open')
    def test_oversized_image_is_rejected_before_transform(self, open_image):
        from django.core.exceptions import ValidationError
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .images import convert_to_webp

        open_image.return_value.width = 4000
        open_image.return_value.height = 4000
        with self.assertRaises(ValidationError):
            convert_to_webp(SimpleUploadedFile('oversized.png', b'test'))

    @override_settings(MINIO_PUBLIC_ENDPOINT_URL='https://media.example.test')
    def test_private_media_urls_are_signed_for_public_host(self):
        from urllib.parse import urlsplit, parse_qs
        from .storage import PrivateMediaStorage

        storage = PrivateMediaStorage(
            bucket_name='private-test-bucket', endpoint_url='http://minio:9000',
            access_key='test-key', secret_key='test-secret', region_name='us-east-1',
        )
        url = urlsplit(storage.url('prescriptions/test.webp'))
        self.assertEqual(url.netloc, 'media.example.test')
        self.assertEqual(url.path, '/private-test-bucket/prescriptions/test.webp')
        query = parse_qs(url.query)
        self.assertIn('X-Amz-Signature', query)
        self.assertEqual(query['X-Amz-Expires'], ['300'])
        self.assertIsNone(storage.custom_domain)
        self.assertEqual(storage.object_parameters['CacheControl'], 'private, no-store')
