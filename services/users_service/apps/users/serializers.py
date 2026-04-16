from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Role

User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "code", "label", "description", "permissions", "created_at", "updated_at"]


class UserSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "profile_photo_url",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
            "updated_at",
            "roles",
        ]


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "phone", "profile_photo_url", "password"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserRoleAssignSerializer(serializers.Serializer):
    role_codes = serializers.ListField(child=serializers.CharField(max_length=50), allow_empty=False)

    def validate_role_codes(self, value):
        existing = set(Role.objects.filter(code__in=value).values_list("code", flat=True))
        missing = [code for code in value if code not in existing]
        if missing:
            raise serializers.ValidationError(f"Roles inexistants: {', '.join(missing)}")
        return value


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "phone", "profile_photo_url", "is_active"]
