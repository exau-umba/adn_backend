from rest_framework import serializers
from .models import Agent, AgentAvailability, AgentSkill


class AgentSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentSkill
        fields = ["name"]


class AgentAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentAvailability
        fields = ["full_time", "part_time", "lodged", "non_lodged"]


class AgentSerializer(serializers.ModelSerializer):
    skills = AgentSkillSerializer(many=True, required=False)
    availability = AgentAvailabilitySerializer(required=False)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Agent
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "city",
            "role",
            "service_category",
            "experience_years",
            "score",
            "status",
            "has_signed_employer_contract",
            "skills",
            "availability",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        skills_data = validated_data.pop("skills", [])
        availability_data = validated_data.pop("availability", None)
        agent = Agent.objects.create(**validated_data)

        for item in skills_data:
            AgentSkill.objects.create(agent=agent, **item)

        if availability_data:
            AgentAvailability.objects.create(agent=agent, **availability_data)

        return agent

    def update(self, instance, validated_data):
        skills_data = validated_data.pop("skills", None)
        availability_data = validated_data.pop("availability", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if skills_data is not None:
            instance.skills.all().delete()
            for item in skills_data:
                AgentSkill.objects.create(agent=instance, **item)

        if availability_data is not None:
            availability, _ = AgentAvailability.objects.get_or_create(agent=instance)
            for attr, value in availability_data.items():
                setattr(availability, attr, value)
            availability.save()

        return instance
