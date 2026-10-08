import django_filters

from tasks.models import Task


class TaskFilter(django_filters.FilterSet):
    due_after = django_filters.DateFilter(field_name="due_date", lookup_expr="gte")
    due_before = django_filters.DateFilter(field_name="due_date", lookup_expr="lte")

    class Meta:
        model = Task
        fields = ["status", "due_after", "due_before"]
