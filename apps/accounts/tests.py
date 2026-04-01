from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import EmailVerification

User = get_user_model()


class EmailVerificationFlowTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="unverified@example.com",
            password="pass12345",
            is_verified=False,
        )

    @patch("apps.accounts.views.send_mail")
    def test_resend_verification_creates_new_token_and_marks_old_unused_tokens_used(
        self, mock_send_mail
    ):
        old_verification = EmailVerification.objects.create(
            user=self.user,
            token="old-token",
            expires_at=timezone.now() + timezone.timedelta(hours=1),
        )

        response = self.client.post(
            reverse("accounts:resend_verification"),
            {"email": self.user.email},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        old_verification.refresh_from_db()
        self.assertTrue(old_verification.is_used)
        self.assertEqual(
            EmailVerification.objects.filter(user=self.user, is_used=False).count(), 1
        )
        self.assertTrue(mock_send_mail.called)

    def test_unverified_user_login_redirects_to_resend_verification(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": self.user.email, "password": "pass12345"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:resend_verification"), response.url)

    @patch("apps.accounts.views.send_mail")
    def test_already_verified_user_is_redirected_to_login_on_resend(self, mock_send_mail):
        self.user.is_verified = True
        self.user.save(update_fields=["is_verified"])

        response = self.client.post(
            reverse("accounts:resend_verification"),
            {"email": self.user.email},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:login"))
        mock_send_mail.assert_not_called()

    @patch("apps.accounts.views.send_mail", side_effect=Exception("smtp failure"))
    def test_resend_verification_shows_error_when_email_send_fails(self, mock_send_mail):
        response = self.client.post(
            reverse("accounts:resend_verification"),
            {"email": self.user.email},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        messages = list(response.context["messages"])
        self.assertTrue(
            any("could not send the verification email" in str(message) for message in messages)
        )
