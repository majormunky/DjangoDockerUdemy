"""
Tests for recipe API's
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)


RECIPE_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Create and return a recipe detail url."""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def create_recipe(user, **kwargs):
    """Create and return a recipe for testing."""
    defaults = {
        "title": "Sample recipe title",
        "time_minutes": 22,
        "price": Decimal("5.25"),
        "description": "Sample Description",
        "link": "http://example.com/recipe.pdf"
    }
    defaults.update(kwargs)
    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


class PublicRecipeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@example.com",
            "testpassword123"
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipe_list_works(self):
        """Test retrieving list of recipies works for a logged in user."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        res = self.client.get(RECIPE_URL)
        all_recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(all_recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user_who_created_works(self):
        """Test that the API returns only recipes for that user."""
        other_user = get_user_model().objects.create_user(
            "test2@example.com",
            "testpassword123"
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)
        recipe_list = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipe_list, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail_works(self):
        """Test get recipe detail."""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)
