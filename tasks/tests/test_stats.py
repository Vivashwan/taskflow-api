import pytest
from django.core.cache import cache
from django.urls import reverse

from tasks.stats import get_task_stats, stats_cache_key

STATS_URL = "task-stats"


@pytest.fixture
def sample_tasks(user, other_user, make_task):
    make_task(user, title="Due today", days_from_today=0, status="todo")
    make_task(user, title="Overdue", days_from_today=-3, status="in-progress")
    make_task(user, title="Overdue but done", days_from_today=-3, status="done")
    make_task(user, title="Future", days_from_today=7, status="todo")
    make_task(other_user, title="Bob's overdue", days_from_today=-1, status="todo")


@pytest.mark.django_db
def test_stats_summarise_own_tasks(auth_client, sample_tasks):
    response = auth_client.get(reverse(STATS_URL))

    assert response.status_code == 200
    assert response.data == {
        "total": 4,
        "by_status": {"todo": 2, "in-progress": 1, "done": 1},
        "overdue": 1,  # done tasks are never overdue
        "due_today": 1,
    }


@pytest.mark.django_db
def test_stats_require_authentication(api_client):
    assert api_client.get(reverse(STATS_URL)).status_code == 401


@pytest.mark.django_db
def test_stats_are_computed_in_one_query(user, sample_tasks, django_assert_num_queries):
    with django_assert_num_queries(1):
        get_task_stats(user)


@pytest.mark.django_db
def test_stats_are_served_from_cache(user, sample_tasks, django_assert_num_queries):
    get_task_stats(user)  # warm the cache

    with django_assert_num_queries(0):
        stats = get_task_stats(user)

    assert stats["total"] == 4


@pytest.mark.django_db
class TestCacheInvalidation:
    def test_creating_a_task_refreshes_stats(self, auth_client, user, sample_tasks, make_task):
        assert auth_client.get(reverse(STATS_URL)).data["total"] == 4

        make_task(user, title="New")

        assert auth_client.get(reverse(STATS_URL)).data["total"] == 5

    def test_updating_a_task_refreshes_stats(self, auth_client, user, make_task):
        task = make_task(user, status="todo")
        assert auth_client.get(reverse(STATS_URL)).data["by_status"]["done"] == 0

        task.status = "done"
        task.save()

        assert auth_client.get(reverse(STATS_URL)).data["by_status"]["done"] == 1

    def test_deleting_a_task_refreshes_stats(self, auth_client, user, make_task):
        task = make_task(user)
        assert auth_client.get(reverse(STATS_URL)).data["total"] == 1

        task.delete()

        assert auth_client.get(reverse(STATS_URL)).data["total"] == 0

    def test_change_only_clears_the_owners_cache(self, user, other_user, make_task):
        get_task_stats(user)
        get_task_stats(other_user)

        make_task(other_user)

        assert cache.get(stats_cache_key(user.id)) is not None
        assert cache.get(stats_cache_key(other_user.id)) is None
