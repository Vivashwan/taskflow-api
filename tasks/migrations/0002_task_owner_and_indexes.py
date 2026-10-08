import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def assign_existing_tasks(apps, schema_editor):
    """Give tasks created before ownership existed to a 'legacy' user, so owner can become NOT NULL."""
    Task = apps.get_model("tasks", "Task")
    if not Task.objects.filter(owner__isnull=True).exists():
        return

    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(app_label, model_name)
    legacy_user, _ = User.objects.get_or_create(username="legacy")
    Task.objects.filter(owner__isnull=True).update(owner=legacy_user)


class Migration(migrations.Migration):
    dependencies = [
        ("tasks", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Add the column as nullable so existing rows stay valid
        migrations.AddField(
            model_name="task",
            name="owner",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tasks",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # 2. Backfill existing rows
        migrations.RunPython(assign_existing_tasks, migrations.RunPython.noop),
        # 3. Enforce NOT NULL now that every row has an owner
        migrations.AlterField(
            model_name="task",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tasks",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddIndex(
            model_name="task",
            index=models.Index(fields=["owner", "status"], name="task_owner_status_idx"),
        ),
        migrations.AddIndex(
            model_name="task",
            index=models.Index(fields=["owner", "due_date"], name="task_owner_due_idx"),
        ),
    ]
