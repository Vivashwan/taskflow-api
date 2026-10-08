from collections import defaultdict
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.timezone import now

from tasks.models import Task


@shared_task
def log_task_action(task_id, action):
    """Log task ID and title to a file."""
    try:
        task = Task.objects.get(id=task_id)
        log_line = f"[{now()}] Task #{task.id} ('{task.title}') was {action} via Celery background task.\n"
    except Task.DoesNotExist:
        log_line = f"[{now()}] ERROR: Task {task_id} not found for action '{action}'\n"

    with open("logs/task_activity.log", "a") as f:
        f.write(log_line)


@shared_task
def send_due_soon_reminders():
    """Email each user one digest of their unfinished tasks due tomorrow. Scheduled daily by Celery beat."""
    tomorrow = timezone.localdate() + timedelta(days=1)
    due_tasks = (
        Task.objects.filter(due_date=tomorrow)
        .exclude(status="done")
        .exclude(owner__email="")
        .select_related("owner")  # one query for tasks + owners, not one per task
        .order_by("owner_id", "title")
    )

    tasks_by_owner = defaultdict(list)
    for task in due_tasks:
        tasks_by_owner[task.owner].append(task)

    for owner, tasks in tasks_by_owner.items():
        lines = "\n".join(f"- {task.title}" for task in tasks)
        send_mail(
            subject=f"{len(tasks)} task(s) due tomorrow",
            message=f"Hi {owner.username},\n\nThese tasks are due on {tomorrow}:\n{lines}\n",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[owner.email],
        )

    return len(tasks_by_owner)
