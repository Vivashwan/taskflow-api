from datetime import timedelta

import pytest
from django.urls import reverse

LIST_URL = "task-list"


def titles(response):
    return [task["title"] for task in response.data["results"]]


@pytest.mark.django_db
class TestFilteringAndOrdering:
    @pytest.fixture(autouse=True)
    def tasks(self, user, make_task):
        make_task(user, title="Write report", days_from_today=5, status="todo")
        make_task(user, title="Fix login bug", days_from_today=1, status="in-progress")
        make_task(user, title="Deploy release", days_from_today=10, status="done")
        make_task(user, title="Review PR", days_from_today=-2, status="todo",
                  description="Check the login changes")

    def test_filter_by_status(self, auth_client):
        response = auth_client.get(reverse(LIST_URL), {"status": "todo"})

        assert sorted(titles(response)) == ["Review PR", "Write report"]

    def test_filter_by_due_date_range(self, auth_client, today):
        response = auth_client.get(
            reverse(LIST_URL),
            {
                "due_after": today.isoformat(),
                "due_before": (today + timedelta(days=5)).isoformat(),
            },
        )

        assert sorted(titles(response)) == ["Fix login bug", "Write report"]

    def test_search_matches_title_and_description(self, auth_client):
        response = auth_client.get(reverse(LIST_URL), {"search": "login"})

        assert sorted(titles(response)) == ["Fix login bug", "Review PR"]

    def test_order_by_due_date(self, auth_client):
        response = auth_client.get(reverse(LIST_URL), {"ordering": "due_date"})

        assert titles(response) == ["Review PR", "Fix login bug", "Write report", "Deploy release"]

    def test_order_by_due_date_descending(self, auth_client):
        response = auth_client.get(reverse(LIST_URL), {"ordering": "-due_date"})

        assert titles(response)[0] == "Deploy release"

    def test_invalid_status_is_rejected(self, auth_client):
        response = auth_client.get(reverse(LIST_URL), {"status": "archived"})

        assert response.status_code == 400


@pytest.mark.django_db
def test_results_are_paginated(auth_client, user, make_task):
    for i in range(12):
        make_task(user, title=f"Task {i}")

    first_page = auth_client.get(reverse(LIST_URL))
    second_page = auth_client.get(reverse(LIST_URL), {"page": 2})

    assert first_page.data["count"] == 12
    assert len(first_page.data["results"]) == 10
    assert first_page.data["next"] is not None
    assert len(second_page.data["results"]) == 2
    assert second_page.data["next"] is None


@pytest.mark.django_db
def test_list_query_count_does_not_grow_with_rows(auth_client, user, make_task,
                                                  django_assert_max_num_queries):
    """Owner is loaded with select_related, so 10 tasks still take a fixed number of queries."""
    for i in range(10):
        make_task(user, title=f"Task {i}")

    # 1 count query for pagination + 1 query for the page of tasks with owners joined
    with django_assert_max_num_queries(2):
        auth_client.get(reverse(LIST_URL))
