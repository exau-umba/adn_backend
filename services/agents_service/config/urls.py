from django.urls import include, path

urlpatterns = [
    path("api/agents/", include("apps.agents.urls")),
    path("health/", include("apps.health.urls")),
]
