from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("recipes", "0001_initial")]
    operations = [
        migrations.RenameField(model_name="recipe", old_name="title", new_name="name"),
        migrations.RenameField(
            model_name="recipe", old_name="description", new_name="text"
        ),
    ]
