from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

from taskflow_api.celery import app as celery_app
from tasks.models import Task


@pytest.fixture(autouse=True)
def isolated_infra(settings):
    """Run Celery tasks inline and use an in-memory cache, so tests need no Redis."""
    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    celery_app.conf.task_always_eager = True
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def today():
    return timezone.localdate()


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        username="alice", email="alice@example.com", password="S3cure-pass!"
    )


@pytest.fixture
def other_user(db):
    return get_user_model().objects.create_user(
        username="bob", email="bob@example.com", password="S3cure-pass!"
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def make_task(today):
    def _make_task(owner, title="Task", days_from_today=1, status="todo", **extra):
        return Task.objects.create(
            owner=owner,
            title=title,
            due_date=today + timedelta(days=days_from_today),
            status=status,
            **extra,
        )

    return _make_task
