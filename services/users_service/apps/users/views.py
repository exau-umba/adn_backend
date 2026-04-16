from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core import signing

from .auth import ADNTokenObtainPairSerializer, build_token_pair
from .models import Role
from .emails import send_activation_email, send_password_setup_email
from .tokens import parse_account_token
from .serializers import (
    AccountActivationSerializer,
    AdminInviteUserSerializer,
    RoleSerializer,
    UserRegisterSerializer,
    UserRoleAssignSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

User = get_user_model()

def serialize_user(request, user):
    return UserSerializer(user, context={"request": request}).data


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        client_role, _ = Role.objects.get_or_create(code="CLIENT", defaults={"label": "Client"})
        user.roles.add(client_role)

        # En environnement local, le premier compte devient admin plateforme.
        if settings.DEBUG and User.objects.count() == 1:
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save(update_fields=["is_staff", "is_superuser", "is_active"])
            admin_role, _ = Role.objects.get_or_create(code="ADMIN", defaults={"label": "Administrateur"})
            user.roles.add(admin_role)
        else:
            mail_error = None
            try:
                send_activation_email(user)
            except Exception as exc:  # pragma: no cover
                mail_error = str(exc)

        if user.is_active:
            token_pair = build_token_pair(user)
            return Response(
                {
                    "user": serialize_user(request, user),
                    "access": token_pair["access"],
                    "refresh": token_pair["refresh"],
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "user": serialize_user(request, user),
                "message": (
                    "Compte créé. Vérifiez votre e-mail pour activer le compte."
                    if not mail_error
                    else f"Compte créé, mais l'e-mail d'activation n'a pas pu être envoyé: {mail_error}"
                ),
            },
            status=status.HTTP_201_CREATED,
        )


class ActivateAccountView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AccountActivationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        password = serializer.validated_data["password"]
        try:
            user_id = parse_account_token(token, "activate")
        except signing.BadSignature:
            return Response({"detail": "Token invalide ou expiré."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "Utilisateur introuvable."}, status=status.HTTP_404_NOT_FOUND)
        user.set_password(password)
        user.is_active = True
        user.save(update_fields=["password", "is_active"])
        token_pair = build_token_pair(user)
        return Response(
            {
                "user": serialize_user(request, user),
                "access": token_pair["access"],
                "refresh": token_pair["refresh"],
            },
            status=status.HTTP_200_OK,
        )


class SetupPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AccountActivationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        password = serializer.validated_data["password"]
        try:
            user_id = parse_account_token(token, "setup-password")
        except signing.BadSignature:
            return Response({"detail": "Token invalide ou expiré."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "Utilisateur introuvable."}, status=status.HTTP_404_NOT_FOUND)
        user.set_password(password)
        user.is_active = True
        user.save(update_fields=["password", "is_active"])
        token_pair = build_token_pair(user)
        return Response(
            {
                "user": serialize_user(request, user),
                "access": token_pair["access"],
                "refresh": token_pair["refresh"],
            },
            status=status.HTTP_200_OK,
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
    mixins.DestroyModelMixin,
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

    @action(detail=False, methods=["post"], url_path="invite")
    def invite(self, request):
        serializer = AdminInviteUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if not user.roles.exists():
            client_role, _ = Role.objects.get_or_create(code="CLIENT", defaults={"label": "Client"})
            user.roles.add(client_role)
        try:
            send_password_setup_email(user)
            message = "Utilisateur créé. E-mail de création de mot de passe envoyé."
        except Exception as exc:  # pragma: no cover
            message = f"Utilisateur créé, mais e-mail non envoyé: {exc}"
        return Response(
            {"user": serialize_user(request, user), "message": message},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="resend-activation")
    def resend_activation(self, request, pk=None):
        user = self.get_object()
        if user.is_active:
            return Response({"detail": "Le compte est déjà actif."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            send_activation_email(user)
            return Response({"detail": "E-mail d'activation renvoyé."}, status=status.HTTP_200_OK)
        except Exception as exc:  # pragma: no cover
            return Response(
                {"detail": f"Impossible d'envoyer l'e-mail: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

    @action(detail=True, methods=["post"], url_path="send-password-setup")
    def send_password_setup(self, request, pk=None):
        user = self.get_object()
        try:
            send_password_setup_email(user)
            return Response({"detail": "E-mail de création de mot de passe envoyé."}, status=status.HTTP_200_OK)
        except Exception as exc:  # pragma: no cover
            return Response(
                {"detail": f"Impossible d'envoyer l'e-mail: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
