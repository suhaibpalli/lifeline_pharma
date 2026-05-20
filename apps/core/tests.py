from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from apps.core.models import (
    ContactInquiry, DeliveryZone, RetailerEnquiry,
    ProductCatalogue, DoctorVisitRequest
)
from decimal import Decimal
import datetime

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
