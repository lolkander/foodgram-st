from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IngredientViewSet, RecipeViewSet, UserAvatarView, CustomUserViewSet

router = DefaultRouter()
router.register("ingredients", IngredientViewSet, basename="ingredients")
router.register("recipes", RecipeViewSet, basename="recipes")
router.register("users", CustomUserViewSet, basename="custom-user")
urlpatterns = [
    path("users/me/avatar/", UserAvatarView.as_view(), name="user-me-avatar")
]
urlpatterns += router.urls
