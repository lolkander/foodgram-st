from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class User(AbstractUser):
    email = models.EmailField("адрес электронной почты", unique=True, max_length=254)
    username = models.CharField(
        "уникальный юзернейм",
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex="^[\\w.@+-]+$",
                message="Имя пользователя может содержать только буквы, цифры и символы @.+-_ (не должно быть пробелов или других специальных символов).",
            )
        ],
    )
    first_name = models.CharField("имя", max_length=150)
    last_name = models.CharField("фамилия", max_length=150)
    avatar = models.ImageField(
        "аватар", upload_to="users/avatars/", null=True, blank=True
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("id",)

    def __str__(self):
        return self.username
