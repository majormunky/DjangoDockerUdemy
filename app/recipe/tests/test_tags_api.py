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
    return Tag.objects.create(user=user, name=name)


def detail_url(tag_id):
    """Create and return a detail tag url."""
    return reverse("recipe:tag-detail", args=[tag_id])


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
        user2 = create_user(email="user2@example.com")
        create_tag("Test", user2)
        my_tag = create_tag("My Item", self.user)

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], my_tag.name)
        self.assertEqual(res.data[0]["id"], my_tag.id)

    def test_update_tag_works(self):
        """Test updating a tag works."""
        tag = create_tag("After Dinner", self.user)

        payload = {
            "name": "Dessert"
        }

        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        tag.refresh_from_db()
        self.assertEqual(tag.name, payload["name"])

    def test_delete_tag_works(self):
        """Test that we can delete a tag."""
        tag = create_tag("Breakfast", self.user)
        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())
