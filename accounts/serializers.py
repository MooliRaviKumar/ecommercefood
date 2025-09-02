from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Profile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "profile_image_url"]


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "password", "role", "profile_image_url"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        Profile.objects.get_or_create(user=user)  # auto-create profile
        return user


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ["id", "user", "phone_number", "address", "created_at"]
        read_only_fields = ["created_at"]
