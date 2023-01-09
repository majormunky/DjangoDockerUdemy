"""
Tests for modifications of admin page
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTests(TestCase):
    """Tests for django admin."""

    def setUp(self):
        """Create user and client"""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            "admin@example.com",
            "testpass123"
        )
        self.user = get_user_model().objects.create_user(
            "user@example.com",
            "testpass123",
            first_name="Test",
            last_name="User"
        )
        self.client.force_login(self.admin_user)

    def test_users_list(self):
        """Test that users are listed on page"""
        url = reverse("admin:core_user_changelist")
        res = self.client.get(url)

        self.assertContains(res, self.user.first_name)
        self.assertContains(res, self.user.last_name)
        self.assertContains(res, self.user.email)
