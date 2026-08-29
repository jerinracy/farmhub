from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.models import User
from apps.farmers.serializers import FarmMiniSerializer, UserMiniSerializer
from apps.farms.models import Farm
from .models import Cow

UserModel = get_user_model()


class CowSerializer(serializers.ModelSerializer):
    farm_detail = FarmMiniSerializer(source="farm", read_only=True)
    farmer_detail = UserMiniSerializer(source="farmer", read_only=True)

    farmer = serializers.PrimaryKeyRelatedField(
        queryset=UserModel.objects.filter(role=User.Role.FARMER),
        required=False,
    )
    farm = serializers.PrimaryKeyRelatedField(
        queryset=Farm.objects.all(),
        required=False,
    )

    class Meta:
        model = Cow
        fields = (
            "id",
            "tag_id",
            "farm",
            "farm_detail",
            "farmer",
            "farmer_detail",
            "breed",
            "gender",
            "date_of_birth",
            "is_active",
            "created_at",
        )
        read_only_fields = (
            "id",
            "farm_detail",
            "farmer_detail",
            "created_at",
        )

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None

        if user:
            if getattr(user, "role", None) == User.Role.FARMER:
                attrs["farmer"] = user
                if hasattr(user, "farmer_profile") and user.farmer_profile.farm:
                    attrs["farm"] = user.farmer_profile.farm
                else:
                    raise serializers.ValidationError(
                        {"farm": "Farmer does not belong to any farm."}
                    )

            elif getattr(user, "role", None) == User.Role.AGENT:
                farmer = attrs.get("farmer")
                if not farmer:
                    if self.instance:
                        farmer = self.instance.farmer
                    else:
                        raise serializers.ValidationError(
                            {"farmer": "Farmer is required when creating a cow."}
                        )

                if (
                    not hasattr(farmer, "farmer_profile")
                    or farmer.farmer_profile.farm.agent != user
                ):
                    raise serializers.ValidationError(
                        {"farmer": "You can only enroll cows for farmers on farms you manage."}
                    )

                attrs["farm"] = farmer.farmer_profile.farm

            elif getattr(user, "role", None) == User.Role.SUPERADMIN or user.is_superuser:
                farmer = attrs.get("farmer")
                farm = attrs.get("farm")
                if not farmer and not self.instance:
                    raise serializers.ValidationError(
                        {"farmer": "Farmer is required when creating a cow."}
                    )
                if farmer and not farm:
                    if hasattr(farmer, "farmer_profile") and farmer.farmer_profile.farm:
                        attrs["farm"] = farmer.farmer_profile.farm

        return attrs
