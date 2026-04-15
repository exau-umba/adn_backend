from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .permissions import HasAgentWriteRole
from .models import Agent, AgentStatus
from .serializers import AgentSerializer
from .tasks import publish_agent_registered_event, publish_agent_status_changed_event


class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.prefetch_related("skills").select_related("availability").all()
    serializer_class = AgentSerializer
    filterset_fields = ["status", "service_category", "city"]
    search_fields = ["first_name", "last_name", "role", "phone"]
    ordering_fields = ["created_at", "score", "experience_years"]
    permission_classes = [IsAuthenticated, HasAgentWriteRole]

    def perform_create(self, serializer):
        agent = serializer.save()
        publish_agent_registered_event.delay(
            {
                "agent_id": str(agent.id),
                "full_name": agent.full_name,
                "service_category": agent.service_category,
                "status": agent.status,
            }
        )

    @action(detail=True, methods=["post"], url_path="suspend")
    def suspend(self, request, pk=None):
        agent = self.get_object()
        agent.status = AgentStatus.SUSPENDED
        agent.save(update_fields=["status", "updated_at"])
        publish_agent_status_changed_event.delay({"agent_id": str(agent.id), "status": agent.status})
        return Response({"detail": "Agent suspendu"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="reactivate")
    def reactivate(self, request, pk=None):
        agent = self.get_object()
        agent.status = AgentStatus.ACTIVE
        agent.save(update_fields=["status", "updated_at"])
        publish_agent_status_changed_event.delay({"agent_id": str(agent.id), "status": agent.status})
        return Response({"detail": "Agent reactive"}, status=status.HTTP_200_OK)
