"""
Tests for models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):
    """Test Models."""

    def test_create_user_with_email_works(self):
        """Test creating user with an email works"""
        email = "test@example.com"
        password = "testpass123"

        user = get_user_model().objects.create_user(email=email, password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Email address gets normalized for a new user"""
        sample_emails = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.com", "TEST3@example.com"],
            ["test4@example.COM", "test4@example.com"]
        ]

        for email, expected_email in sample_emails:
            test_user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(test_user.email, expected_email)

    def test_new_user_without_email_raises_error(self):
        """Creating a user without an email raises ValueError"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "sample123")
            
