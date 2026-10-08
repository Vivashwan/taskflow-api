from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from tasks.models import Task
from tasks.stats import invalidate_task_stats
from tasks.tasks import log_task_action


@receiver(post_save, sender=Task)
def task_created_handler(sender, instance, created, **kwargs):
    if created:
        log_task_action.delay(instance.id, "created")


@receiver(post_save, sender=Task)
@receiver(post_delete, sender=Task)
def invalidate_stats_on_change(sender, instance, **kwargs):
    invalidate_task_stats(instance.owner_id)
