from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


def _role_codes_for_user(user):
    return list(user.roles.values_list("code", flat=True))


class ADNTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["roles"] = _role_codes_for_user(user)
        token["username"] = user.username
        return token


def build_token_pair(user):
    refresh = ADNTokenObtainPairSerializer.get_token(user)
    access = refresh.access_token
    return {"access": str(access), "refresh": str(refresh)}
