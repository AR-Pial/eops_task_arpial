from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.test_helpers import auth_client, make_user

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user_defaults_to_customer(self):
        user = User.objects.create_user(email="a@example.com", password="password123")
        self.assertEqual(user.user_type, User.UserType.CUSTOMER)
        self.assertTrue(user.check_password("password123"))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_user_requires_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="password123")

    def test_create_superuser_is_superadmin(self):
        user = User.objects.create_superuser(
            email="admin@example.com", password="password123"
        )
        self.assertEqual(user.user_type, User.UserType.SUPERADMIN)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_email_must_be_unique(self):
        User.objects.create_user(email="dup@example.com", password="password123")
        with self.assertRaises(IntegrityError):
            User.objects.create_user(email="dup@example.com", password="password123")

    def test_str_returns_email(self):
        user = make_user(email="show@example.com")
        self.assertEqual(str(user), "show@example.com")


class AuthAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_returns_token_and_customer_user(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "new@example.com",
                "password": "password123",
                "first_name": "Ada",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["email"], "new@example.com")
        self.assertEqual(response.data["user"]["user_type"], "customer")
        self.assertTrue(Token.objects.filter(key=response.data["token"]).exists())

    def test_register_rejects_short_password(self):
        response = self.client.post(
            "/api/auth/register/",
            {"email": "short@example.com", "password": "short"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_ignores_user_type_in_payload(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "role@example.com",
                "password": "password123",
                "user_type": "admin",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="role@example.com")
        self.assertEqual(user.user_type, User.UserType.CUSTOMER)

    def test_login_success(self):
        make_user(email="login@example.com", password="password123")
        response = self.client.post(
            "/api/auth/login/",
            {"email": "login@example.com", "password": "password123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["email"], "login@example.com")

    def test_login_invalid_credentials(self):
        make_user(email="login@example.com", password="password123")
        response = self.client.post(
            "/api/auth/login/",
            {"email": "login@example.com", "password": "wrongpass"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_requires_auth(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_get_and_patch(self):
        user = make_user(email="me@example.com", first_name="Old")
        client = auth_client(user)

        get_resp = client.get("/api/auth/me/")
        self.assertEqual(get_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(get_resp.data["email"], "me@example.com")

        patch_resp = client.patch(
            "/api/auth/me/",
            {"first_name": "New", "phone": "01700000000", "user_type": "admin"},
            format="json",
        )
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_resp.data["first_name"], "New")
        self.assertEqual(patch_resp.data["phone"], "01700000000")
        user.refresh_from_db()
        self.assertEqual(user.user_type, User.UserType.CUSTOMER)
        self.assertEqual(user.email, "me@example.com")
