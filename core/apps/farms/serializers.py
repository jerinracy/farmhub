from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Farm

User = get_user_model()


class AgentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
        )
        read_only_fields = fields


class FarmSerializer(serializers.ModelSerializer):
    agent = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.AGENT),
        required=False,
        allow_null=True,
    )
    agent_detail = AgentDetailSerializer(
        source="agent",
        read_only=True,
    )

    class Meta:
        model = Farm
        fields = (
            "id",
            "name",
            "location",
            "agent",
            "agent_detail",
            "created_by",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_by",
            "created_at",
            "updated_at",
        )
