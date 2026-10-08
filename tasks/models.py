from django.conf import settings
from django.db import models


class Task(models.Model):
    STATUS_CHOICES = [
        ("todo", "To Do"),
        ("in-progress", "In Progress"),
        ("done", "Done"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="todo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Every list query is scoped to one owner, then filtered by status or due date
        indexes = [
            models.Index(fields=["owner", "status"], name="task_owner_status_idx"),
            models.Index(fields=["owner", "due_date"], name="task_owner_due_idx"),
        ]

    def __str__(self):
        return self.title
