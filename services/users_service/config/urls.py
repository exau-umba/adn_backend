from django.urls import include, path

urlpatterns = [
    path("", include("django_prometheus.urls")),
    path("api/users/", include("apps.users.urls")),
    path("health/", include("apps.health.urls")),
]
