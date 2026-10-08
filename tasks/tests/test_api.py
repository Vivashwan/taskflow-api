import pytest
from django.urls import reverse
from django.utils import timezone

from tasks.models import Task


def detail_url(task):
    return reverse("task-detail", args=[task.id])


@pytest.mark.django_db
def test_create_task(auth_client, user):
    url = reverse("task-list")
    data = {
        "title": "Test Task",
        "due_date": timezone.localdate(),
    }

    response = auth_client.post(url, data, format="json")
    assert response.status_code == 201
    assert Task.objects.count() == 1
    assert Task.objects.first().title == "Test Task"
    assert Task.objects.first().owner == user
    assert response.data["owner"] == "alice"


@pytest.mark.django_db
def test_create_ignores_owner_in_payload(auth_client, user, other_user):
    response = auth_client.post(
        reverse("task-list"),
        {"title": "Mine", "due_date": timezone.localdate(), "owner": other_user.id},
        format="json",
    )

    assert response.status_code == 201
    assert Task.objects.get().owner == user


@pytest.mark.django_db
def test_create_rejects_blank_title(auth_client):
    response = auth_client.post(
        reverse("task-list"), {"title": "   ", "due_date": timezone.localdate()}, format="json"
    )

    assert response.status_code == 400
    assert "title" in response.data


@pytest.mark.django_db
def test_get_tasks(auth_client, user, make_task):
    make_task(user, title="Task 1")
    make_task(user, title="Task 2")
    url = reverse("task-list")
    response = auth_client.get(url)
    assert response.status_code == 200
    assert response.data["count"] == 2


@pytest.mark.django_db
def test_list_shows_only_own_tasks(auth_client, user, other_user, make_task):
    make_task(user, title="Mine")
    make_task(other_user, title="Not mine")

    response = auth_client.get(reverse("task-list"))

    titles = [task["title"] for task in response.data["results"]]
    assert titles == ["Mine"]


@pytest.mark.django_db
def test_update_own_task(auth_client, user, make_task):
    task = make_task(user)

    response = auth_client.patch(detail_url(task), {"status": "done"}, format="json")

    assert response.status_code == 200
    task.refresh_from_db()
    assert task.status == "done"


@pytest.mark.django_db
class TestOtherUsersTasksAreHidden:
    """Another user's task must look like it does not exist (404), so IDs can't be probed."""

    def test_cannot_read(self, auth_client, other_user, make_task):
        task = make_task(other_user)
        assert auth_client.get(detail_url(task)).status_code == 404

    def test_cannot_update(self, auth_client, other_user, make_task):
        task = make_task(other_user, title="Original")

        response = auth_client.patch(detail_url(task), {"title": "Hacked"}, format="json")

        assert response.status_code == 404
        task.refresh_from_db()
        assert task.title == "Original"

    def test_cannot_delete(self, auth_client, other_user, make_task):
        task = make_task(other_user)

        response = auth_client.delete(detail_url(task))

        assert response.status_code == 404
        assert Task.objects.filter(id=task.id).exists()
