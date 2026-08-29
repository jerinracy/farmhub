from rest_framework import serializers

from apps.cattle.models import Cow

from .models import MilkProduction


class MilkProductionSerializer(serializers.ModelSerializer):
    cow_tag_id = serializers.CharField(source="cow.tag_id", read_only=True)
    farm_name = serializers.CharField(source="farm.name", read_only=True)
    farmer_username = serializers.CharField(source="farmer.username", read_only=True)

    cow = serializers.PrimaryKeyRelatedField(
        queryset=Cow.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = MilkProduction
        fields = (
            "id",
            "cow",
            "cow_tag_id",
            "farm",
            "farm_name",
            "farmer",
            "farmer_username",
            "date",
            "quantity_liters",
            "session",
            "recorded_at",
        )
        read_only_fields = (
            "id",
            "cow_tag_id",
            "farm",
            "farm_name",
            "farmer",
            "farmer_username",
            "recorded_at",
        )
        validators = []

    def validate(self, attrs):
        view = self.context.get("view")
        cow = attrs.get("cow")
        if not cow and view and hasattr(view, "get_cow"):
            cow = view.get_cow()

        date = attrs.get("date", getattr(self.instance, "date", None))
        session = attrs.get("session", getattr(self.instance, "session", None))

        if cow and date and session:
            existing = MilkProduction.objects.filter(
                cow=cow,
                date=date,
                session=session,
            )
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise serializers.ValidationError(
                    "Milk record already exists for this cow, date, and session."
                )

        return attrs
