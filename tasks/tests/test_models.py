from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from tasks.models import Task


# @pytest.mark.django_db allows DB access in your test.
@pytest.mark.django_db
def test_task_creation(user):
    task = Task.objects.create(owner=user, title="Testing", due_date=timezone.localdate())
    assert task.id is not None
    assert task.title == "Testing"
    assert task.status == "todo"
    assert str(task) == "Testing"


@pytest.mark.django_db
def test_deleting_user_deletes_their_tasks(user, make_task):
    make_task(user)
    user.delete()
    assert Task.objects.count() == 0


@pytest.mark.django_db
def test_migrations_match_models():
    """Fails if a model change was made without a matching migration."""
    call_command("makemigrations", "--check", "--dry-run", stdout=StringIO())
