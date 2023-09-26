from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework.serializers import (IntegerField, ModelSerializer,
                                        PrimaryKeyRelatedField, ReadOnlyField,
                                        SerializerMethodField, ValidationError)
from rest_framework.validators import UniqueTogetherValidator
from users.models import Follow, User

from .validators import ValidateColor, ValidateUsername


class UserSerializer(ValidateUsername, ModelSerializer):
    """Сериализатор для отображения User."""

    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed'
        )
        extra_kwargs = {'password': {'write_only': True}}
        read_only_fields = ('is_subscribed',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = self.context.get('request').user
        if not request or request.user.is_anonymous:
            return False
        return obj.following.filter(user=user, author=obj).exists()


class UserCreateSerializer(ValidateUsername, ModelSerializer):
    """Сериализатор для создания User."""

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password'
        )


class TagSerializer(ValidateColor, ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = (
            'id', 'name',
            'color', 'slug'
        )
        read_only_fields = ('__all__',)


class IngredientSerializer(ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = ('__all__',)


class GetRecipeIngredientSerializer(ModelSerializer):
    """Сериализатор ингредиентов для модели RecipeIngredient."""

    id = ReadOnlyField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class RecipeSerializer(ModelSerializer):
    """Сериализатор для безопасного доступа к модели Recipe."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = GetRecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    is_in_shopping_cart = SerializerMethodField(read_only=True)
    is_favorited = SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe

        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )

    def get_is_favorited(self, object):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return request.user.favorites.filter(recipe=object).exists()

    def get_is_in_shopping_cart(self, object):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return request.user.shopping_cart.filter(recipe=object).exists()


class ShortRecipeResponseSerializer(ModelSerializer):
    """Короткий отображение рецептов при создании подписки."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('__all__',)


class FollowListSerializer(UserSerializer):
    """Краткий ответ при успешной подписке."""

    recipes = ShortRecipeResponseSerializer(many=True, read_only=True)
    recipes_count = SerializerMethodField()
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )
        read_only_fields = ('__all__',)

    def get_recipes_count(self, object):
        return object.recipes.count()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = self.context.get('request').user
        if not request or request.user.is_anonymous:
            return False
        return obj.following.filter(user=user, author=obj).exists()


class FollowSerializer(ModelSerializer):
    """Сериализатор для модели Follow."""

    def validate_author(self, user):
        author = self.context.get('request').user
        if user == author:
            raise ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        return user

    class Meta:
        model = Follow
        fields = ('user', 'author')
        read_only_fields = ('__all__',)

        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны.'
            )
        ]

    def to_representation(self, instance):
        return FollowListSerializer(
            instance.author,
            context={'request': self.context.get('request')}
        ).data


class CreateRecipeIngredientSerializer(ModelSerializer):
    """Сериализатор для ингредиентов при создании рецепта."""

    id = IntegerField()
    amount = IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount'
        )


class CreateRecipeSerializer(ModelSerializer):
    """Сериализатор для небезопасного доступа к модели Recipe."""

    author = UserSerializer(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    ingredients = CreateRecipeIngredientSerializer(many=True)

    def to_representation(self, instance):
        return RecipeSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }
        ).data

    def validate_ingredients(self, ingredients):
        ingredients_data = [
            ingredient.get('id') for ingredient in ingredients
        ]
        if len(ingredients_data) != len(set(ingredients_data)):
            raise ValidationError(
                'Ингредиенты рецепта не должны повторятся.'
            )
        return ingredients

    def validate_tags(self, tags):
        if len(tags) != len(set(tags)):
            raise ValidationError(
                'Теги рецепта не должны повторятся.'
            )
        return tags

    def add_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(
                ingredient=get_object_or_404(
                    Ingredient,
                    id=ingredient['id']),
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients_data]
        )

    def create(self, validated_data):
        image = validated_data.pop('image')
        author = self.context.get('request').user
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        # Вернула как было, иначе не работало :(
        recipe = Recipe.objects.create(
            author=author,
            image=image,
            **validated_data
        )
        recipe.tags.set(tags_data)
        self.add_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        super().update(instance, validated_data)
        instance.tags.clear()
        instance.ingredients.clear()
        instance.tags.set(tags)
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.add_ingredients(instance, ingredients)
        return instance

    class Meta:
        model = Recipe
        fields = (
            'id', 'author',
            'ingredients', 'tags',
            'image', 'name',
            'text', 'cooking_time'
        )
        read_only_fields = ('__all__',)


class FavoriteSerializer(ModelSerializer):
    """Сериализатор для модели Favorite."""

    class Meta:
        model = Favorite
        fields = '__all__'
        read_only_fields = ('__all__',)
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Вы уже добавляли это рецепт в избранное.'
            )
        ]


class ShoppingCartSerializer(ModelSerializer):
    """Сериализатор для модели ShoppingCart."""

    class Meta:
        model = ShoppingCart
        fields = '__all__'
        read_only_fields = ('__all__',)
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Этот рецепт уже в списке покупок.'
            )
        ]


class SubscriptionShowSerializer(UserSerializer):
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username',
            'first_name', 'last_name',
            'email', 'is_subscribed',
            'recipes', 'recipes_count'
        )
        read_only_fields = ('__all__',)

    def get_recipes(self, object):
        recipes_limit = self.context.get('recipes_limit')
        if recipes_limit:
            recipes_limit = int(recipes_limit)
        author_recipes = object.recipes.all()[:recipes_limit]
        return ShortRecipeResponseSerializer(
            author_recipes, many=True
        ).data

    def get_recipes_count(self, object):
        return object.recipes.count()
