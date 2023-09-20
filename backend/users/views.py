from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.paginations import PageNumberPagination
from api.serializers import (
    SubscriptionShowSerializer, FollowSerializer
)

from .models import Follow, User


class FollowViewSet(UserViewSet):
    """Вьюсет класса Follow."""

    pagination_class = PageNumberPagination

    @action(methods=['get'], detail=False)
    def subscription_list(self, request):
        recipes_limit = request.query_params.get('recipes_limit')
        authors = User.objects.filter(following__user=request.user)
        result_pages = self.paginate_queryset(queryset=authors)
        serializer = SubscriptionShowSerializer(
            result_pages,
            context={
                'request': request,
                'recipes_limit': recipes_limit
            },
            many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(methods=['post', 'delete'], detail=True)
    def subscribe(self, request, id=None):
        followed_user = get_object_or_404(User, id=id)
        serializer = FollowSerializer(
            data={
                'user': request.user.id,
                'following': followed_user.id
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if request.method == 'DELETE':
            subscription = Follow.objects.filter(
                user=request.user,
                following=followed_user
            )
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': 'Вы уже отписались или не были подписаны'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
