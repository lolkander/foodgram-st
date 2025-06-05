from django.contrib import admin
from .models import (
    Ingredient,
    Tag,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart,
    Follow,
)
from django.db.models import Count


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit")
    search_fields = ("name",)
    list_filter = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "color")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ("name",)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "get_author_username",
        "cooking_time",
        "pub_date",
        "get_times_favorited",
    )
    search_fields = ("name", "author__username", "author__email")
    list_filter = ("author__username", "name", "tags")
    inlines = (RecipeIngredientInline,)
    readonly_fields = ("get_times_favorited_display", "pub_date")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(times_favorited=Count("favorited_by"))
        return queryset

    @admin.display(description="Автор", ordering="author__username")
    def get_author_username(self, obj):
        return obj.author.username

    @admin.display(description="В избранном (раз)", ordering="times_favorited")
    def get_times_favorited(self, obj):
        return obj.times_favorited

    @admin.display(description="Добавлено в избранное (раз)")
    def get_times_favorited_display(self, obj):
        if hasattr(obj, "times_favorited"):
            return obj.times_favorited
        return Favorite.objects.filter(recipe=obj).count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ("recipe", "ingredient", "amount")
    list_filter = ("recipe__name", "ingredient__name")
    search_fields = ("recipe__name", "ingredient__name")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe", "date_added")
    search_fields = ("user__username", "user__email", "recipe__name")
    list_filter = ("user__username", "recipe__name")
    autocomplete_fields = ("user", "recipe")


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe", "date_added")
    search_fields = ("user__username", "user__email", "recipe__name")
    list_filter = ("user__username", "recipe__name")
    autocomplete_fields = ("user", "recipe")


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("user", "author", "date_followed")
    search_fields = (
        "user__username",
        "user__email",
        "author__username",
        "author__email",
    )
    list_filter = ("user__username", "author__username")
    autocomplete_fields = ("user", "author")
