# app_autenticacao/serializers.py

from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)


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


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Customiza o TokenObtainPairSerializer para incluir o username na resposta.
    """
    def validate(self, attrs):
        # Chama a validação padrão para obter os tokens (access e refresh)
        data = super().validate(attrs)
        
        # Adiciona o username ao payload de resposta
        data["username"] = self.user.username
        return data


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Customiza o TokenRefreshSerializer para incluir o username na resposta do refresh.
    """
    def validate(self, attrs):
        # Chama a validação padrão para renovar os tokens
        data = super().validate(attrs)

        # Decodifica o RefreshToken para obter o username
        refresh = RefreshToken(attrs["refresh"])
        data["username"] = refresh.get("username")
        return data

