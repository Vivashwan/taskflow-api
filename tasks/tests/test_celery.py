import os

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from tasks.models import Task
from tasks.tasks import log_task_action, send_due_soon_reminders


@pytest.mark.django_db
def test_log_task_action(user):
    # Ensure log directory exists
    os.makedirs("logs", exist_ok=True)
    task = Task.objects.create(owner=user, title="CeleryTest", due_date=timezone.localdate())
    log_task_action(task.id, "created")

    # Check the log file for correct entry
    with open("logs/task_activity.log") as f:
        log_lines = f.readlines()
        assert any("CeleryTest" in line for line in log_lines)


@pytest.mark.django_db
def test_log_task_action_handles_missing_task():
    os.makedirs("logs", exist_ok=True)
    log_task_action(999999, "created")

    with open("logs/task_activity.log") as f:
        assert any("Task 999999 not found" in line for line in f)


@pytest.mark.django_db
class TestDueSoonReminders:
    def test_sends_one_digest_per_user(self, user, other_user, make_task, mailoutbox):
        make_task(user, title="Pay invoice", days_from_today=1)
        make_task(user, title="Call client", days_from_today=1, status="in-progress")
        make_task(other_user, title="Bob's task", days_from_today=1)

        sent = send_due_soon_reminders()

        assert sent == 2
        assert len(mailoutbox) == 2
        alice_mail = next(m for m in mailoutbox if m.to == ["alice@example.com"])
        assert alice_mail.subject == "2 task(s) due tomorrow"
        assert "Pay invoice" in alice_mail.body
        assert "Call client" in alice_mail.body
        assert "Bob's task" not in alice_mail.body

    def test_skips_done_tasks_and_other_dates(self, user, make_task, mailoutbox):
        make_task(user, title="Already done", days_from_today=1, status="done")
        make_task(user, title="Due today", days_from_today=0)
        make_task(user, title="Next week", days_from_today=7)

        assert send_due_soon_reminders() == 0
        assert mailoutbox == []

    def test_skips_users_without_email(self, make_task, mailoutbox):
        no_email = get_user_model().objects.create_user(username="noemail", password="x")
        make_task(no_email, days_from_today=1)

        assert send_due_soon_reminders() == 0
        assert mailoutbox == []

    def test_loads_tasks_and_owners_in_one_query(self, user, other_user, make_task,
                                                 django_assert_num_queries):
        for owner in (user, other_user):
            for i in range(3):
                make_task(owner, title=f"Task {i}", days_from_today=1)

        with django_assert_num_queries(1):
            send_due_soon_reminders()

    def test_runs_through_celery(self, user, make_task, mailoutbox):
        make_task(user, days_from_today=1)

        result = send_due_soon_reminders.delay()

        assert result.get() == 1
        assert len(mailoutbox) == 1


@pytest.mark.django_db
def test_task_creation_triggers_background_logging(user, monkeypatch):
    calls = []
    monkeypatch.setattr(log_task_action, "delay", lambda *args: calls.append(args))

    task = Task.objects.create(owner=user, title="Signal test", due_date=timezone.localdate())

    assert calls == [(task.id, "created")]
