"""
Tests for the ingredients API
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse("recipe:ingredient-list")


def create_user(email="test@example.com", password="testpassword123"):
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientsApiTests(TestCase):
    """Tests for un-authentiated api requests."""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required_works(self):
        """Test that authentication is required."""
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Test authenticated requests."""
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list_works(self):
        Ingredient.objects.create(user=self.user, name="Kale")
        Ingredient.objects.create(user=self.user, name="Vanilla")

        res = self.client.get(INGREDIENTS_URL)

        ingredient_list = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredient_list, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        test_user = create_user(email="test2@example.com")
        Ingredient.objects.create(user=test_user, name="Test User Ingredient")

        Ingredient.objects.create(user=self.user, name="Banana")
        Ingredient.objects.create(user=self.user, name="Chocolate")

        res = self.client.get(INGREDIENTS_URL)

        ingredient_list = Ingredient.objects.filter(user=self.user).order_by("-name")
        serializer = IngredientSerializer(ingredient_list, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
