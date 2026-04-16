from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import ActivateAccountView, LoginView, MeView, RegisterView, RoleViewSet, SetupPasswordView, UserViewSet

router = DefaultRouter()
router.register(r"roles", RoleViewSet, basename="roles")
router.register(r"accounts", UserViewSet, basename="accounts")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/activate/", ActivateAccountView.as_view(), name="auth-activate"),
    path("auth/setup-password/", SetupPasswordView.as_view(), name="auth-setup-password"),
    path("auth/login/", LoginView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("", include(router.urls)),
]
