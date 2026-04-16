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
    profile_photo_url = serializers.SerializerMethodField()

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

    def get_profile_photo_url(self, obj):
        if not getattr(obj, "profile_photo", None):
            return ""
        try:
            url = obj.profile_photo.url
        except Exception:
            return ""
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    profile_photo = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "phone", "profile_photo", "password"]

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
    profile_photo = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "phone", "profile_photo", "is_active"]
