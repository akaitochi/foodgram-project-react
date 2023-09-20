from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser import utils, views
from djoser.conf import settings
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .filters import IngredientSearchFilter, RecipeFilter
from .paginations import LimitPageNumberPagination
from .download_in_pdf import create_pdf_file
from .permissions import IsAuthorOrReadOnly, IsAdminOrReadOnly
from .serializers import (
    CreateRecipeSerializer,
    CreateResponseSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    TagSerializer
)
from recipes.models import (
    Favorite,
    Ingredient,
    RecipeIngredient,
    Recipe,
    ShoppingCart,
    Tag
)


class CustomTokenCreateView(views.TokenCreateView):
    """Вьюсет для получения токена."""

    def _action(self, serializer):
        super()._action(serializer)
        token = utils.login_user(self.request, serializer.user)
        # Здесь не уверена, достанется ли serializers из settings
        token_serializer_class = settings.SERIALIZERS.token
        return Response(
            data=token_serializer_class(token).data,
            status=status.HTTP_201_CREATED
        )


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет класса Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет класса Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientSearchFilter
    permission_classes = (permissions.AllowAny,)


class RecipeViewSet(ModelViewSet):
    """Вьюсет класса Recipe."""

    queryset = Recipe.objects.select_related('author')
    permission_classes = (
        IsAdminOrReadOnly, IsAuthorOrReadOnly
    )
    pagination_class = LimitPageNumberPagination
    filterset_class = RecipeFilter
    filter_backends = [DjangoFilterBackend, ]

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeSerializer
        return CreateRecipeSerializer

    @staticmethod
    def post_for_shopping_cart_and_favorite(request, pk, serializer_req):
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {'user': request.user.id, 'recipe': pk}
        serializer = serializer_req(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer_data = CreateResponseSerializer(recipe)
        return Response(serializer_data.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def delete_for_shopping_cart_and_favorite(request, pk, location, model):
        recipe = get_object_or_404(Recipe, pk=pk)
        obj = model.objects.filter(
            user=request.user,
            recipe=recipe
        )
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': f'Рецепт уже удален из {location}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(methods=['post', 'delete'], detail=True)
    def favorite(self, request, pk):
        if request.method == 'POST':
            return self.post_for_shopping_cart_and_favorite(
                request, pk, FavoriteSerializer
            )
        return self.delete_for_shopping_cart_and_favorite(
            request, pk, 'избранного', Favorite
        )

    @action(methods=['post', 'delete'], detail=True,)
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return self.post_for_shopping_cart_and_favorite(
                request, pk, ShoppingCartSerializer
            )
        return self.delete_for_shopping_cart_and_favorite(
            request, pk, 'списка покупок', ShoppingCart
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        total_ingredient_amount = Sum('amount')
        shopping_cart = (
            RecipeIngredient.objects.filter(
                recipe__shopping_cart__user=request.user
            ).values(
                'ingredient__name',
                'ingredient__measurement_unit',
            ).order_by(
                'ingredient__name'
            ).annotate(total_ingredient_amount)
        )
        return create_pdf_file(shopping_cart)
