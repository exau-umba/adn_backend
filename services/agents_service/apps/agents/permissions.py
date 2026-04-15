from rest_framework.permissions import SAFE_METHODS, BasePermission


class HasAgentWriteRole(BasePermission):
    """
    Lecture ouverte a tout utilisateur authentifie.
    Ecriture reservee aux roles metier autorises.
    """

    allowed_roles = {"ADMIN", "RH_MANAGER", "OPERATIONS_MANAGER"}

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)

        token_roles = request.auth.get("roles", []) if request.auth else []
        return any(role in self.allowed_roles for role in token_roles)
