"""
Tests for recipe API's
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import (
    Recipe,
    Tag,
    Ingredient,
)
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


def create_user(**kwargs):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**kwargs)


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
        self.user = create_user(
            email="test@example.com",
            password="testpassword123"
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
        other_user = create_user(
            email="test2@example.com",
            password="testpassword123"
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

    def test_create_recipe_works(self):
        """Test that creating a recipe over the API works."""
        payload = {
            "title": "Sample Recipe",
            "time_minutes": 30,
            "price": Decimal("5.99"),
        }
        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update_works(self):
        """Test partial update of a recipe."""
        original_link = "http://example.com/recipe.pdf"
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link=original_link
        )

        payload = {'title': 'New Recipe Title'}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update_works(self):
        """Test full update of recipe."""
        recipe = create_recipe(
            user=self.user,
            title="Sample recipe title",
            link="https://www.example.com/recipe.pdf",
            description="A description of a recipe"
        )

        payload = {
            "title": "A new title",
            "link": "https://www.example.com/new-recipe.pdf",
            "description": "A different description",
            "price": Decimal("10.05"),
            "time_minutes": 20
        }
        res = self.client.put(detail_url(recipe.id), payload)

        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, payload['link'])
        self.assertEqual(recipe.description, payload['description'])
        self.assertEqual(recipe.price, payload['price'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.user, self.user)

    def test_unable_to_change_user_on_recipe_works(self):
        # Create second user
        new_user = create_user(
            email="user2@example.com",
            password="testtest123"
        )

        # Create recipe for the first user
        recipe = create_recipe(user=self.user)

        # Try to assign that to the new user
        payload = {"user": new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        # Update recipe data from database
        recipe.refresh_from_db()

        # The user still should be the same
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe_works(self):
        """Test that we can delete one of our recipes."""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_fails(self):
        """Test that we can't delete another user's recipe."""
        new_user = create_user(email="test1@example.com", password="testpass123")
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags_works(self):
        """Test creating a new recipe with new tags."""
        payload = {
            "title": "Thai Prawn Curry",
            "time_minutes": 30,
            "price": Decimal("2.50"),
            "tags": [{"name": "Thai"}, {"name": "Dinner"}],
        }
        res = self.client.post(RECIPE_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload["tags"]:
            tag_exists = recipe.tags.filter(
                name=tag["name"],
                user=self.user
            ).exists()
            self.assertTrue(tag_exists)

    def test_new_tag_with_existing_tag_reuses_tag(self):
        """Test creating recipe with existing tag."""
        tag_taco = Tag.objects.create(name="Taco", user=self.user)
        payload = {
            "title": "Street Taco",
            "time_minutes": 30,
            "price": Decimal("3.50"),
            "tags": [{"name": "Taco"}, {"name": "Street Food"}]
        }
        res = self.client.post(RECIPE_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]

        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_taco, recipe.tags.all())
        for tag in payload["tags"]:
            tag_exists = recipe.tags.filter(
                name=tag["name"],
                user=self.user
            ).exists()
            self.assertTrue(tag_exists)

    def test_create_tag_on_update_works(self):
        """Test creating a tag when updating a recipe."""
        recipe = create_recipe(user=self.user)
        payload = {"tags": [{"name": "Lunch"}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_tag = Tag.objects.get(user=self.user, name="Lunch")
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tags_works(self):
        """Test we can assign an existing tag on update."""
        tag_breakfast = Tag.objects.create(name="Breakfast", user=self.user)
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(name="Lunch", user=self.user)
        payload = {"tags": [{"name": "Lunch"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())

        # Patch will replace data instead of updating it
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags_works(self):
        """Test that we can clear the tags for a recipe."""
        tag = Tag.objects.create(name="Test Tag", user=self.user)
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {"tags": []}

        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_creating_ingredient_with_recipe_works(self):
        """Test that we can create a new ingredient with a recipe."""
        payload = {
            "title": "Cauliflower Tacos",
            "time_minutes": 60,
            "price": Decimal("4.39"),
            "ingredients": [{"name": "Cauliflower"}, {"name": "Salt"}],
        }
        res = self.client.post(RECIPE_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(len(recipes), 1)
        recipe = recipes.first()

        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload["ingredients"]:
            exists = recipe.ingredients.filter(name=ingredient["name"]).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient_works(self):
        """Test that when creating a new recipe, we re-use an existing ingredient."""
        lemon_ingredient = Ingredient.objects.create(user=self.user, name="Lemon")
        payload = {
            "title": "Vietnamese Soup",
            "time_minutes": 35,
            "price": Decimal("2.50"),
            "ingredients": [{"name": "Lemon"}, {"name": "Fish Sauce"}]
        }

        res = self.client.post(RECIPE_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes.first()

        for ingredient in payload["ingredients"]:
            exists = Ingredient.objects.filter(
                user=self.user,
                name=ingredient["name"]
            ).exists()
            self.assertTrue(exists)

        self.assertIn(lemon_ingredient, recipe.ingredients.all())

    def test_create_ingredient_on_update_works(self):
        """Test creating ingredient when updating recipe."""
        recipe = create_recipe(user=self.user)
        payload = {
            'ingredients': [
                {"name": "Lemon"},
            ]
        }
        # initially we have no ingredients
        self.assertEqual(recipe.ingredients.count(), 0)

        # update recipe
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        # we should now have one ingredient
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 1)

        # check that its the ingredient we expect
        new_ingredient = Ingredient.objects.get(user=self.user, name=payload["ingredients"][0]["name"])
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_with_existing_ingredient_works(self):
        """Test that if we update a recipe with an ingredient that already exists, it works."""
        lemon_ingredient = Ingredient.objects.create(user=self.user, name="Lemon")
        lime_ingredient = Ingredient.objects.create(user=self.user, name="Lime")
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(lemon_ingredient)

        payload = {"ingredients": [{"name": "Lime"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 1)
        self.assertNotIn(lemon_ingredient, recipe.ingredients.all())
        self.assertIn(lime_ingredient, recipe.ingredients.all())

    def test_clearing_ingredient_list_works(self):
        """Test that we can clear an ingredient list for a recipe."""
        recipe = create_recipe(user=self.user)
        lemon_ingredient = Ingredient.objects.create(user=self.user, name="Lemon")
        lime_ingredient = Ingredient.objects.create(user=self.user, name="Lime")

        recipe.ingredients.add(lemon_ingredient)
        recipe.ingredients.add(lime_ingredient)

        self.assertEqual(recipe.ingredients.count(), 2)

        payload = {"ingredients": []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(recipe.ingredients.count(), 0)
