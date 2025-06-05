from django.contrib.auth import get_user_model
from rest_framework import serializers
from recipes.models import (
    Ingredient,
    Tag,
    RecipeIngredient,
    Recipe,
    Favorite,
    ShoppingCart,
    Follow,
)
from .fields import Base64ImageField
from djoser import serializers as djoser_serializers

User = get_user_model()


class CustomUserCreateSerializer(djoser_serializers.UserCreateSerializer):

    class Meta(djoser_serializers.UserCreateSerializer.Meta):
        model = User
        fields = ("email", "id", "username", "password", "first_name", "last_name")


class CustomCurrentUserSerializer(djoser_serializers.UserSerializer):
    avatar = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta(djoser_serializers.UserSerializer.Meta):
        fields = djoser_serializers.UserSerializer.Meta.fields + (
            "avatar",
            "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated or request.user == obj:
            return False
        return Follow.objects.filter(user=request.user, author=obj).exists()

    def get_avatar(self, obj):
        request = self.context.get("request")
        if obj.avatar and hasattr(obj.avatar, "url"):
            if request:
                host = request.get_host()
                scheme = request.scheme
                port = request.get_port()
                if ":" not in host and port not in ("80", "443"):
                    host_with_port = f"{host}:{port}"
                else:
                    host_with_port = host
                avatar_path = obj.avatar.url
                if not avatar_path.startswith("/"):
                    avatar_path = f"/{avatar_path}"
                return f"{scheme}://{host_with_port}{avatar_path}"
            return obj.avatar.url
        return None


class UserAvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField()


class UserAvatarResponseSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("avatar",)

    def get_avatar(self, obj):
        request = self.context.get("request")
        if obj.avatar and hasattr(obj.avatar, "url"):
            if request:
                host = request.get_host()
                scheme = request.scheme
                port = request.get_port()
                if ":" not in host and port not in ("80", "443"):
                    host_with_port = f"{host}:{port}"
                else:
                    host_with_port = host
                avatar_path = obj.avatar.url
                if not avatar_path.startswith("/"):
                    avatar_path = f"/{avatar_path}"
                return f"{scheme}://{host_with_port}{avatar_path}"
            return obj.avatar.url
        return None


class UserRecipeSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Follow.objects.filter(user=request.user, author=obj).exists()
        return False

    def get_avatar(self, obj):
        request = self.context.get("request")
        if obj.avatar and hasattr(obj.avatar, "url"):
            if request:
                host = request.get_host()
                scheme = request.scheme
                port = request.get_port()
                if ":" not in host and port not in ("80", "443"):
                    host_with_port = f"{host}:{port}"
                else:
                    host_with_port = host
                avatar_path = obj.avatar.url
                if not avatar_path.startswith("/"):
                    avatar_path = f"/{avatar_path}"
                manual_uri = f"{scheme}://{host_with_port}{avatar_path}"
                return manual_uri
            return obj.avatar.url
        return None


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
        read_only_fields = fields


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")
        read_only_fields = fields


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(source="ingredient.measurement_unit")

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserRecipeSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        many=True, read_only=True, source="recipeingredients"
    )
    image = Base64ImageField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()
        return False


class RecipeMutationResponseSerializer(serializers.ModelSerializer):
    author = UserRecipeSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        many=True, read_only=True, source="recipeingredients"
    )
    image = Base64ImageField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()
        return False


class RecipeIngredientWriteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)


class RecipeWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=False, allow_empty=True
    )
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "tags", "ingredients", "name", "image", "text", "cooking_time")
        read_only_fields = ("id",)

    def validate_ingredients(self, ingredients_data):
        if not ingredients_data:
            raise serializers.ValidationError(
                "Хотя бы один ингредиент должен быть указан."
            )
        ingredient_ids = []
        for item in ingredients_data:
            ingredient_id = item["id"].id
            if ingredient_id in ingredient_ids:
                raise serializers.ValidationError("Ингредиенты не должны повторяться.")
            ingredient_ids.append(ingredient_id)
        return ingredients_data

    def validate_tags(self, tags_data):
        if tags_data:
            tag_ids = [tag.id for tag in tags_data]
            if len(tag_ids) != len(set(tag_ids)):
                raise serializers.ValidationError("Теги не должны повторяться.")
        return tags_data

    def validate(self, attrs):
        if self.partial and "ingredients" not in self.initial_data:
            raise serializers.ValidationError(
                {"ingredients": ["Это поле обязательно для обновления рецепта."]}
            )
        return attrs

    def _create_or_update_ingredients(self, recipe, ingredients_data):
        if recipe.ingredients.exists():
            RecipeIngredient.objects.filter(recipe=recipe).delete()
        recipe_ingredients_to_create = []
        for ingredient_data in ingredients_data:
            ingredient_obj = ingredient_data["id"]
            amount = ingredient_data["amount"]
            recipe_ingredients_to_create.append(
                RecipeIngredient(
                    recipe=recipe, ingredient=ingredient_obj, amount=amount
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients_to_create)

    def create(self, validated_data):
        tags_data = validated_data.pop("tags", [])
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self._create_or_update_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop("tags", None)
        ingredients_data = validated_data.pop("ingredients", None)
        instance.name = validated_data.get("name", instance.name)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )
        if "image" in validated_data:
            instance.image = validated_data.get("image", instance.image)
        instance.save()
        if tags_data is not None:
            instance.tags.set(tags_data)
        if ingredients_data is not None:
            self._create_or_update_ingredients(instance, ingredients_data)
        return instance

    def to_representation(self, instance):
        request = self.context.get("request")
        return RecipeMutationResponseSerializer(
            instance, context={"request": request}
        ).data


class FollowSerializer(UserRecipeSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserRecipeSerializer.Meta):
        fields = UserRecipeSerializer.Meta.fields + ("recipes", "recipes_count")

    def get_is_subscribed(self, obj):
        return True

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes_limit = None
        if request and request.query_params.get("recipes_limit"):
            try:
                recipes_limit = int(request.query_params.get("recipes_limit"))
            except ValueError:
                pass
        recipes_queryset = obj.recipes.all()
        if recipes_limit is not None and recipes_limit > 0:
            recipes_queryset = recipes_queryset[:recipes_limit]
        serializer = RecipeReadSerializer(
            recipes_queryset, many=True, context=self.context
        )
        return serializer.data


class RecipeInFollowSerializer(serializers.ModelSerializer):
    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = fields


class FollowSerializer(UserRecipeSerializer):
    recipes = RecipeInFollowSerializer(many=True, read_only=True, source="recipes")
    recipes_count = serializers.IntegerField(source="recipes.count", read_only=True)

    class Meta(UserRecipeSerializer.Meta):
        fields = UserRecipeSerializer.Meta.fields + ("recipes", "recipes_count")

    def get_is_subscribed(self, obj):
        return True


class FollowSerializer(UserRecipeSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source="recipes.count", read_only=True)

    class Meta(UserRecipeSerializer.Meta):
        fields = UserRecipeSerializer.Meta.fields + ("recipes", "recipes_count")

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes_limit = None
        if request and request.query_params.get("recipes_limit"):
            try:
                recipes_limit = int(request.query_params.get("recipes_limit"))
                if recipes_limit < 0:
                    recipes_limit = None
            except ValueError:
                pass
        recipes_queryset = obj.recipes.all()
        if recipes_limit is not None:
            recipes_queryset = recipes_queryset[:recipes_limit]
        serializer = RecipeInFollowSerializer(
            recipes_queryset, many=True, context=self.context
        )
        return serializer.data


class ShortLinkSerializer(serializers.Serializer):
    short_link = serializers.CharField(source="short-link")


class FollowCreateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), default=serializers.CurrentUserDefault()
    )
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Follow
        fields = ("user", "author")

    def validate(self, data):
        user = data["user"]
        author = data["author"]
        if user == author:
            raise serializers.ValidationError(
                "Вы не можете подписаться на самого себя."
            )
        return data
