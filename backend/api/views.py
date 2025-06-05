from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, filters
from recipes.models import (
    Ingredient,
    Tag,
    Recipe,
    RecipeIngredient,
    Follow,
    Favorite,
    ShoppingCart,
)
from .serializers import (
    IngredientSerializer,
    TagSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    FollowSerializer,
    RecipeInFollowSerializer,
    CustomCurrentUserSerializer,
    UserAvatarSerializer,
    CustomUserCreateSerializer,
    FollowCreateSerializer,
    UserAvatarResponseSerializer,
)
from rest_framework import permissions, status
from rest_framework.response import Response
from .permissions import IsAuthorOrAdminOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from .filters import RecipeFilter
from djoser import views as djoser_views
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from django.db import IntegrityError
from django.http import HttpResponse
from django.db.models import Sum
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView

User = get_user_model()


class RecipePagination(PageNumberPagination):
    page_size_query_param = "limit"

    def get_page_size(self, request):
        page_size = None
        if self.page_size_query_param:
            try:
                page_size_str = request.query_params.get(self.page_size_query_param)
                if page_size_str is not None:
                    page_size = int(page_size_str)
                    if page_size <= 0:
                        page_size = None
                    elif self.max_page_size and page_size > self.max_page_size:
                        page_size = self.max_page_size
            except (ValueError, KeyError):
                page_size = None
        if page_size is None:
            page_size_attr = getattr(self, "page_size", None)
            if page_size_attr is None:
                page_size_attr = settings.REST_FRAMEWORK.get("PAGE_SIZE", 10)
            page_size = page_size_attr
        return page_size


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = []
    pagination_class = None

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        search_name = self.request.query_params.get("name", None)
        if search_name:
            queryset = queryset.filter(name__istartswith=search_name)
        return queryset


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = []
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by("-pub_date")
    permission_classes = [IsAuthorOrAdminOrReadOnly]
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_class = RecipeFilter
    pagination_class = RecipePagination

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[permissions.AllowAny],
        url_path="get-link",
    )
    def get_short_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link_value = f"http://myfoodgram.test/r/{recipe.id}"
        return Response({"short-link": short_link_value}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        current_user = request.user
        if request.method == "POST":
            if Favorite.objects.filter(user=current_user, recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже в избранном."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Favorite.objects.create(user=current_user, recipe=recipe)
            serializer = RecipeInFollowSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == "DELETE":
            favorite_instance = Favorite.objects.filter(
                user=current_user, recipe=recipe
            ).first()
            if not favorite_instance:
                return Response(
                    {"errors": "Этого рецепта нет в вашем избранном."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            favorite_instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        current_user = request.user
        if request.method == "POST":
            if ShoppingCart.objects.filter(user=current_user, recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ShoppingCart.objects.create(user=current_user, recipe=recipe)
            serializer = RecipeInFollowSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == "DELETE":
            cart_item = ShoppingCart.objects.filter(
                user=current_user, recipe=recipe
            ).first()
            if not cart_item:
                return Response(
                    {"errors": "Этого рецепта нет в вашем списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        current_user = request.user
        ingredients_summary = (
            RecipeIngredient.objects.filter(
                recipe__in_shopping_cart_of__user=current_user
            )
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
            .order_by("ingredient__name")
        )
        if not ingredients_summary:
            empty_list_content = "Ваш список покупок пуст.\n"
            response = HttpResponse(
                empty_list_content, content_type="text/plain; charset=utf-8"
            )
            response["Content-Disposition"] = (
                'attachment; filename="empty_shopping_list.txt"'
            )
            return response
        shopping_list_content = "Список покупок Фудграм:\n\n"
        for item in ingredients_summary:
            shopping_list_content += f"- {item['ingredient__name']} ({item['ingredient__measurement_unit']}) - {item['total_amount']}\n"
        response = HttpResponse(
            shopping_list_content, content_type="text/plain; charset=utf-8"
        )
        response["Content-Disposition"] = 'attachment; filename="shopping_list.txt"'
        return response


class CustomUserViewSet(djoser_views.UserViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return CustomUserCreateSerializer
        return super().get_serializer_class()

    @action(
        methods=["get", "put", "patch", "delete"],
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=CustomCurrentUserSerializer,
        url_path="me",
    )
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        if request.method == "GET":
            return self.retrieve(request, *args, **kwargs)
        elif request.method == "PUT":
            return self.update(request, *args, **kwargs)
        elif request.method == "PATCH":
            return self.partial_update(request, *args, **kwargs)
        elif request.method == "DELETE":
            return self.destroy(request, *args, **kwargs)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if request.method == "POST":
            if user == author:
                return Response(
                    {"errors": "Вы не можете подписаться на самого себя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if Follow.objects.filter(user=user, author=author).exists():
                return Response(
                    {"errors": "Вы уже подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer_create = FollowCreateSerializer(
                data={"user": user.id, "author": author.id},
                context={"request": request},
            )
            serializer_create.is_valid(raise_exception=True)
            serializer_create.save()
            response_serializer = FollowSerializer(author, context={"request": request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == "DELETE":
            subscription = Follow.objects.filter(user=user, author=author)
            if not subscription.exists():
                return Response(
                    {"errors": "Вы не были подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        subscribed_authors = User.objects.filter(following__user=user).distinct()
        paginator = PageNumberPagination()
        paginator.page_size = request.query_params.get(
            "limit", settings.REST_FRAMEWORK.get("PAGE_SIZE")
        )
        page = paginator.paginate_queryset(subscribed_authors, request)
        serializer = FollowSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class UserAvatarView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = UserAvatarResponseSerializer(user, context={"request": request})
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = UserAvatarSerializer(data=request.data)
        if serializer.is_valid():
            if user.avatar and hasattr(user.avatar, "delete"):
                user.avatar.delete(save=False)
            user.avatar = serializer.validated_data["avatar"]
            user.save(update_fields=["avatar"])
            response_serializer = UserAvatarResponseSerializer(
                user, context={"request": request}
            )
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        user = request.user
        if user.avatar and hasattr(user.avatar, "delete"):
            user.avatar.delete(save=False)
            user.avatar = None
            user.save(update_fields=["avatar"])
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": "У пользователя нет аватара для удаления."},
            status=status.HTTP_404_NOT_FOUND,
        )
