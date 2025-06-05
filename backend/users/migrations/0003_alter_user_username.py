import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("users", "0002_user_avatar")]
    operations = [
        migrations.AlterField(
            model_name="user",
            name="username",
            field=models.CharField(
                max_length=150,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Имя пользователя может содержать только буквы, цифры и символы @.+-_ (не должно быть пробелов или других специальных символов).",
                        regex="^[\\w.@+-]+$",
                    )
                ],
                verbose_name="уникальный юзернейм",
            ),
        )
    ]
