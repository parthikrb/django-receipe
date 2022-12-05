"""
Test for the user API.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test public feature of the api"""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test Creating successful user"""
        payload = {
            'email': 'test@this.com',
            'password': 'test@123',
            'name': 'Test name'
        }

        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', response.data)

    def test_user_with_email_exists_error(self):
        """Test user creation with existing email"""
        payload = {
            'email': 'this@that.com',
            'password': 'this@123',
            'name': 'Test Name'
        }

        create_user(**payload)

        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_with_short_password_error(self):
        """Test user creation with short password error"""
        payload = {
            'email': 'this@that.com',
            'password': '123',
            'name': 'Test Name'
        }

        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test token generation for valid credentials"""
        user_details = {
            'email': 'this@that.com',
            'password': 'pass@123',
            'name': 'Test Name'
        }

        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password']
        }

        response = self.client.post(TOKEN_URL, payload)
        self.assertIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test error thrown for bad credentials"""
        user_details = {
            'email': 'this@that.com',
            'password': 'goodPass',
            'name': 'Test Name'
        }

        create_user(**user_details)

        payload = {'email': user_details['email'], 'password': 'badPass'}

        response = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_credentials(self):
        """Test error thrown for blank credentials"""

        payload = {'email': 'this.that@this.com', 'password': ''}

        response = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_user_unauthorized(self):
        """Test authentication is required for users"""

        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserAPITests(TestCase):
    """Test API request that require authentication"""

    def setUp(self):
        self.user = create_user(email='test@test.com',
                                password='pass@123',
                                name='Test Name')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile(self):
        """"Test retrieving logged in user details"""
        response = self.client.get(ME_URL)
        self.assertEqual(response.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def test_me_post_not_allowed(self):
        """Test post request not allowed on me"""
        response = self.client.post(ME_URL, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_modify_user_name(self):
        """Test modification of user's name"""
        payload = {'name': 'Hello After', 'password': 'newpassword'}

        response = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
