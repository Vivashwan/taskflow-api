import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.mark.django_db
class TestRegistration:
    def test_register_creates_user_with_hashed_password(self, api_client):
        response = api_client.post(
            reverse("register"),
            {"username": "carol", "email": "carol@example.com", "password": "S3cure-pass!"},
            format="json",
        )

        assert response.status_code == 201
        assert "password" not in response.data
        user = get_user_model().objects.get(username="carol")
        assert user.password != "S3cure-pass!"
        assert user.check_password("S3cure-pass!")

    def test_register_rejects_weak_password(self, api_client):
        response = api_client.post(
            reverse("register"),
            {"username": "carol", "password": "123"},
            format="json",
        )

        assert response.status_code == 400
        assert "password" in response.data

    def test_register_rejects_duplicate_username(self, api_client, user):
        response = api_client.post(
            reverse("register"),
            {"username": user.username, "password": "S3cure-pass!"},
            format="json",
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestJwtAuth:
    def test_token_grants_access_to_tasks(self, api_client, user):
        token = api_client.post(
            reverse("token_obtain_pair"),
            {"username": "alice", "password": "S3cure-pass!"},
            format="json",
        )
        assert token.status_code == 200

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.data['access']}")
        response = api_client.get(reverse("task-list"))

        assert response.status_code == 200

    def test_refresh_token_issues_new_access_token(self, api_client, user):
        tokens = api_client.post(
            reverse("token_obtain_pair"),
            {"username": "alice", "password": "S3cure-pass!"},
            format="json",
        ).data

        response = api_client.post(
            reverse("token_refresh"), {"refresh": tokens["refresh"]}, format="json"
        )

        assert response.status_code == 200
        assert "access" in response.data

    def test_wrong_password_gets_no_token(self, api_client, user):
        response = api_client.post(
            reverse("token_obtain_pair"),
            {"username": "alice", "password": "wrong"},
            format="json",
        )

        assert response.status_code == 401

    def test_anonymous_request_is_rejected(self, api_client):
        assert api_client.get(reverse("task-list")).status_code == 401

    def test_invalid_token_is_rejected(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer not-a-real-token")
        assert api_client.get(reverse("task-list")).status_code == 401
