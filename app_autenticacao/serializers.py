# app_autenticacao/serializers.py

from django.contrib.auth.models import User
from rest_framework import serializers

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
            "is_active",
            "is_superuser",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class AutenticacaoSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()
    username = serializers.CharField()
