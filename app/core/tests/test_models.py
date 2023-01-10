"""
Tests for models
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models


def create_user(email="test@example.com", password="testpass123", **kwargs):
    """Create and return a user."""
    return get_user_model().objects.create_user(email=email, password=password, **kwargs)


class ModelTests(TestCase):
    """Test Models."""

    def test_create_user_with_email_works(self):
        """Test creating user with an email works"""
        email = "test@example.com"
        password = "testpass123"

        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

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
            test_user = get_user_model().objects.create_user(
                email,
                'sample123'
            )
            self.assertEqual(test_user.email, expected_email)

    def test_new_user_without_email_raises_error(self):
        """Creating a user without an email raises ValueError"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "sample123")

    def test_create_superuser_works(self):
        """Test creating a super user works"""
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test123'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe_works(self):
        user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass123'
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title="Sample recipe name",
            time_minutes=5,
            price=Decimal("5.50"),
            description="Sample description"
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag_works(self):
        user = create_user()
        tag = models.Tag.objects.create(user=user, name="Tag1")
        self.assertEqual(str(tag), tag.name)
