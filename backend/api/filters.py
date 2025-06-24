from django_filters import rest_framework as filters
from recipes.models import Recipe, Tag
from django.contrib.auth import get_user_model

User = get_user_model()


class MultipleValueCharFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class RecipeFilter(filters.FilterSet):
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    tags = filters.ModelMultipleChoiceFilter(
        field_name="tags__slug", to_field_name="slug", queryset=Tag.objects.all()
    )
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(method="filter_is_in_shopping_cart")

    class Meta:
        model = Recipe
        fields = ["author", "tags"]

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated:
            if value:
                return queryset.filter(favorited_by__user=self.request.user)
            return queryset.exclude(favorited_by__user=self.request.user)
        if value:
            return queryset.none()
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated:
            if value:
                return queryset.filter(in_shopping_cart_of__user=self.request.user)
            return queryset.exclude(in_shopping_cart_of__user=self.request.user)
        if value:
            return queryset.none()
        return queryset
