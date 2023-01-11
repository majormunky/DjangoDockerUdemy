"""
Tests for the tag API
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Tag
from recipe.serializers import TagSerializer


TAGS_URL = reverse("recipe:tag-list")


def create_user(email="user@example.com", password="testpassword123"):
    """Create and return a user."""
    return get_user_model().objects.create_user(email=email, password=password)


def create_tag(name, user):
    """Create and return a tag."""
    return Tag.objects.create(user=self.user, name=name)


class PublicTagsApiTests(TestCase):
    """Test public api requests."""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required_works(self):
        """Test auth is required to retrieve tags through API."""
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test private api requests."""
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_get_tags_works(self):
        """Test that we can get a list of tags through the API."""
        create_tag("Vegan", self.user)
        create_tag("Dessert", self.user)

        res = self.client.get(TAGS_URL)

        tag_list = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tag_list, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_tags_limited_to_user_works(self):
        """Test that we can only get tags we create."""
        user2 = create_user()
        create_tag("Test", user2)
        my_tag = create_tag("My Item", self.user)

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], my_tag.name)
        self.assertEqual(res.data[0]["id"], my_tag.id)
