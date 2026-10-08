from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone

from tasks.models import Task

STATS_CACHE_TIMEOUT = 300  # seconds


def stats_cache_key(user_id):
    return f"task-stats:{user_id}"


def get_task_stats(user):
    """Return a user's task summary, served from Redis when cached."""
    key = stats_cache_key(user.id)
    stats = cache.get(key)
    if stats is None:
        stats = compute_task_stats(user)
        cache.set(key, stats, STATS_CACHE_TIMEOUT)
    return stats


def compute_task_stats(user):
    """Compute every count in a single aggregate query instead of one query per metric."""
    today = timezone.localdate()
    open_tasks = ~Q(status="done")

    counts = Task.objects.filter(owner=user).aggregate(
        total=Count("id"),
        todo=Count("id", filter=Q(status="todo")),
        in_progress=Count("id", filter=Q(status="in-progress")),
        done=Count("id", filter=Q(status="done")),
        overdue=Count("id", filter=open_tasks & Q(due_date__lt=today)),
        due_today=Count("id", filter=open_tasks & Q(due_date=today)),
    )

    return {
        "total": counts["total"],
        "by_status": {
            "todo": counts["todo"],
            "in-progress": counts["in_progress"],
            "done": counts["done"],
        },
        "overdue": counts["overdue"],
        "due_today": counts["due_today"],
    }


def invalidate_task_stats(user_id):
    cache.delete(stats_cache_key(user_id))
