from rest_framework.serializers import (
    SerializerMethodField, ModelSerializer)

from api.validators import ValidateUsername
from .models import Follow, User


class UserSerializer(ValidateUsername, ModelSerializer):
    """Сериализатор для отображения User."""

    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Follow.objects.filter(
            user=request.user, following=obj).exists()


class UserCreateSerializer(ValidateUsername, ModelSerializer):
    """Сериализатор для создания User."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password'
        )
