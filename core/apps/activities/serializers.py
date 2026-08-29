from rest_framework import serializers

from apps.cattle.models import Cow
from .models import CowActivity


class CowActivitySerializer(serializers.ModelSerializer):
    cow_tag_id = serializers.CharField(source="cow.tag_id", read_only=True)
    recorded_by_username = serializers.CharField(
        source="recorded_by.username", read_only=True
    )
    cow = serializers.PrimaryKeyRelatedField(
        queryset=Cow.objects.all(),
        required=False,
    )

    class Meta:
        model = CowActivity
        fields = (
            "id",
            "cow",
            "cow_tag_id",
            "activity_type",
            "date",
            "notes",
            "details",
            "recorded_by",
            "recorded_by_username",
            "created_at",
        )
        read_only_fields = (
            "id",
            "cow_tag_id",
            "recorded_by",
            "recorded_by_username",
            "created_at",
        )
