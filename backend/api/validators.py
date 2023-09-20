import re

from django.core.exceptions import ValidationError


class ValidateUsername:
    """Валидатор имени пользователя."""

    def validate_username(self, value):
        """Проверяем, что нельзя использовать 'me' в качестве username."""

        if value.lower() == 'me':
            raise ValidationError(
                'Пользователя с username "me" нельзя создавать'
            )
        if not re.match(r"^[\w.@+-]+\Z", value):
            raise ValidationError(
                'username содержит недопустимые символы'
            )
        return value


class ValidateColor:
    """Валидатор для цвета HEX."""

    def validate_color(self, value):
        """Проверяем, что цвет в формате HEX."""

        if not re.match(r"^[-a-zA-Z0-9_]+\z", value):
            raise ValidationError(
                'Введённое значения должно быть в формате HEX'
            )
        return value
