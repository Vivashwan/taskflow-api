from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from tasks.filters import TaskFilter
from tasks.models import Task
from tasks.serializers import RegisterSerializer, TaskSerializer
from tasks.stats import get_task_stats


def home_view(request):
    return HttpResponse("Welcome to TaskFlow API")


class RegisterView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TaskFilter
    search_fields = ["title", "description"]
    ordering_fields = ["due_date", "created_at", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        # Users only ever see their own tasks; other users' tasks return 404, not 403
        return Task.objects.filter(owner=self.request.user).select_related("owner")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        return Response(get_task_stats(request.user))
