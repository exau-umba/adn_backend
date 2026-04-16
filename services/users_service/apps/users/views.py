from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .auth import ADNTokenObtainPairSerializer, build_token_pair
from .models import Role
from .serializers import RoleSerializer, UserRegisterSerializer, UserRoleAssignSerializer, UserSerializer, UserUpdateSerializer

User = get_user_model()

def serialize_user(request, user):
    return UserSerializer(user, context={"request": request}).data


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # En environnement local, le premier compte devient admin plateforme.
        if settings.DEBUG and User.objects.count() == 1:
            user.is_staff = True
            user.is_superuser = True
            user.save(update_fields=["is_staff", "is_superuser"])
            admin_role, _ = Role.objects.get_or_create(code="ADMIN", defaults={"label": "Administrateur"})
            user.roles.add(admin_role)

        token_pair = build_token_pair(user)
        return Response(
            {
                "user": serialize_user(request, user),
                "access": token_pair["access"],
                "refresh": token_pair["refresh"],
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    serializer_class = ADNTokenObtainPairSerializer


class MeView(APIView):
    def get(self, request):
        return Response(serialize_user(request, request.user))


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().order_by("code")
    serializer_class = RoleSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["code", "label", "description"]
    ordering_fields = ["code", "label", "created_at", "updated_at"]
    ordering = ["code"]


class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.prefetch_related("roles").all().order_by("username")
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["username", "email", "first_name", "last_name", "roles__code", "roles__label"]
    ordering_fields = ["username", "email", "date_joined", "last_login", "updated_at"]
    ordering = ["username"]

    def get_serializer_class(self):
        if self.action in {"update", "partial_update"}:
            return UserUpdateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        instance.refresh_from_db()
        return Response(serialize_user(request, instance), status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="assign-roles")
    def assign_roles(self, request, pk=None):
        serializer = UserRoleAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.get_object()
        roles = Role.objects.filter(code__in=serializer.validated_data["role_codes"])
        user.roles.set(roles)

        return Response(serialize_user(request, user), status=status.HTTP_200_OK)
