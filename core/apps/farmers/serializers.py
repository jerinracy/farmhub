from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from apps.farms.models import Farm
from .models import FarmerProfile

User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "phone_number",
        )
        read_only_fields = fields


class FarmMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farm
        fields = (
            "id",
            "name",
        )
        read_only_fields = fields


class FarmerListSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    farm = FarmMiniSerializer(read_only=True)

    class Meta:
        model = FarmerProfile
        fields = (
            "id",
            "user",
            "farm",
            "national_id",
            "address",
            "onboarded_by",
            "joined_at",
        )
        read_only_fields = fields


class FarmerOnboardSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )
    phone_number = serializers.CharField(write_only=True, required=False, allow_blank=True)

    user = UserMiniSerializer(read_only=True)
    farm_detail = FarmMiniSerializer(source="farm", read_only=True)

    class Meta:
        model = FarmerProfile
        fields = (
            "id",
            "username",
            "email",
            "password",
            "phone_number",
            "farm",
            "national_id",
            "address",
            "user",
            "farm_detail",
            "onboarded_by",
            "joined_at",
        )
        read_only_fields = (
            "id",
            "user",
            "farm_detail",
            "onboarded_by",
            "joined_at",
        )

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        farm = attrs.get("farm")

        if request and request.user.is_authenticated:
            if getattr(request.user, "role", None) == User.Role.AGENT:
                if farm and farm.agent != request.user:
                    raise serializers.ValidationError(
                        {"farm": "You can only onboard farmers to farms you manage."}
                    )

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        onboarded_by = request.user if request and request.user.is_authenticated else None

        username = validated_data.pop("username")
        email = validated_data.pop("email", "")
        password = validated_data.pop("password")
        phone_number = validated_data.pop("phone_number", "")

        farm = validated_data.pop("farm")
        national_id = validated_data.pop("national_id", "")
        address = validated_data.pop("address", "")

        with transaction.atomic():
            user = User(
                username=username,
                email=email,
                phone_number=phone_number,
                role=User.Role.FARMER,
                is_active=True,
                created_by=onboarded_by,
            )
            user.set_password(password)
            user.save()

            farmer_profile = FarmerProfile.objects.create(
                user=user,
                farm=farm,
                national_id=national_id,
                address=address,
                onboarded_by=onboarded_by,
            )

        return farmer_profile


class FarmerUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = FarmerProfile
        fields = (
            "id",
            "farm",
            "national_id",
            "address",
            "email",
            "phone_number",
            "joined_at",
        )
        read_only_fields = (
            "id",
            "joined_at",
        )

    def validate(self, attrs):
        request = self.context.get("request")
        farm = attrs.get("farm")

        if request and request.user.is_authenticated:
            if getattr(request.user, "role", None) == User.Role.AGENT:
                if farm and farm.agent != request.user:
                    raise serializers.ValidationError(
                        {"farm": "You can only transfer farmers to farms you manage."}
                    )
        return attrs

    def update(self, instance, validated_data):
        email = validated_data.pop("email", None)
        phone_number = validated_data.pop("phone_number", None)

        if email is not None or phone_number is not None:
            user = instance.user
            if email is not None:
                user.email = email
            if phone_number is not None:
                user.phone_number = phone_number
            user.save()

        return super().update(instance, validated_data)
