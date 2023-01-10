"""
Tests for the user API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**kwargs):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**kwargs)


class PublicUserAPITests(TestCase):
    """Test the public features of the user API."""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_works(self):
        """Test that creating a user works."""
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "John",
            "last_name": "Doe"
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_create_user_fails_with_duplicate_email(self):
        """Test if user can be created with an email that already exists"""
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "John",
            "last_name": "Doe"
        }
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_with_short_password_fails(self):
        """Test if user can create a user with a short password."""
        payload = {
            "email": "test@example.com",
            "password": "123",
            "first_name": "John",
            "last_name": "Doe"
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user_works(self):
        """Test generates token for user with valid credentials."""
        user_details = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "test@example.com",
            "password": "testpass1234"
        }
        create_user(**user_details)
        payload = {
            'email': user_details['email'],
            'password': user_details['password']
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_with_incorrect_details_fails(self):
        """Test that trying to get a token with incorrect details fails"""
        user_details = {
            "email": "test@example.com",
            "password": "goodpass1234"
        }
        create_user(
            email=user_details['email'],
            password=user_details['password']
        )
        payload = {
            "email": user_details['email'],
            "password": "incorrect-password"
        }

        res = self.client.post(TOKEN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_with_missing_password_fails(self):
        """Test that trying to get a token with incorrect details fails"""
        user_details = {
            "email": "test@example.com",
            "password": "goodpass1234"
        }
        create_user(
            email=user_details['email'],
            password=user_details['password']
        )
        payload = {
            "email": user_details['email'],
            "password": ""
        }

        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized_fails(self):
        """Test authentication is required for /me endpoint."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Tests for API requests that require authentication."""
    def setUp(self):
        self.user = create_user(
            email="test@example.com",
            password="testpass1234",
            first_name="John",
            last_name="Doe"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_profile_for_logged_in_user_works(self):
        """Test getting the profile for the logged in user."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'email': self.user.email
        })

    def test_post_me_fails(self):
        """POST request is not allowed for me endpoint."""
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile_works(self):
        """Test updating user profile works."""
        payload = {'first_name': 'Johnathan', 'password': 'newpassword123'}
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()

        self.assertEqual(self.user.first_name, payload['first_name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res, status.HTTP_200_OK)
