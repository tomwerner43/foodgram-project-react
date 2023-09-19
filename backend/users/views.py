from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Subscribe, User
from .serializers import SubscribeSerializer


class SubscriptionsViewSet(viewsets.ModelViewSet):
    """
    Используется для отображения и управления подписками пользователя.
    """

    serializer_class = SubscribeSerializer
    permission_classes = (IsAuthenticated, )
    pagination_class = LimitOffsetPagination
    http_method_names = ('get', )

    def get_queryset(self):
        user = self.request.user.pk
        return Subscribe.objects.filter(user=user)


class SubscribeAddDelView(APIView):
    """
    Используется для добавления и удаления подписок на других пользователей.
    """

    permission_classes = (IsAuthenticated, )
    http_method_names = ('post', 'delete', )

    def post(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        if request.user == author:
            return Response(
                {'errors': 'Подписываться на самого себя нельзя!'},
                status=status.HTTP_400_BAD_REQUEST)
        sub_status = Subscribe.objects.filter(user=request.user, author=author)
        if sub_status:
            return Response(
                {'errors': f'Подписка на {author.username} уже есть!'},
                status=status.HTTP_400_BAD_REQUEST)
        queryset = Subscribe.objects.create(user=request.user, author=author)
        serializer = SubscribeSerializer(
            queryset, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        sub_status = Subscribe.objects.filter(user=request.user, author=author)
        if not sub_status:
            return Response(
                {'errors': 'Вы не отслеживаете этого автора!'},
                status=status.HTTP_400_BAD_REQUEST)
        sub_status.delete()
        return Response(
            {'success': f'Вы успешно отписались от {author.username}!'},
            status=status.HTTP_204_NO_CONTENT
        )
