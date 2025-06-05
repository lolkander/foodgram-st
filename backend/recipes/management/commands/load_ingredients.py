import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Загружает ингредиенты из CSV файла (data/ingredients.csv) в базу данных."

    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR.parent, "data", "ingredients.csv")
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"Файл не найден: {file_path}"))
            return
        self.stdout.write(
            self.style.SUCCESS(f"Начинаю загрузку ингредиентов из {file_path}")
        )
        loaded_count = 0
        skipped_count = 0
        try:
            with open(file_path, mode="r", encoding="utf-8") as csv_file:
                reader = csv.reader(csv_file)
                for row in reader:
                    if not row:
                        continue
                    try:
                        name = row[0].strip()
                        measurement_unit = row[1].strip()
                        if not name or not measurement_unit:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Пропущена строка с неполными данными: {row}"
                                )
                            )
                            skipped_count += 1
                            continue
                        (obj, created) = Ingredient.objects.get_or_create(
                            name=name, defaults={"measurement_unit": measurement_unit}
                        )
                        if created:
                            loaded_count += 1
                        else:
                            if obj.measurement_unit != measurement_unit:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'Ингредиент "{name}" уже существует с другой единицей измерения: "{obj.measurement_unit}" вместо "{measurement_unit}". Не обновлен.'
                                    )
                                )
                            skipped_count += 1
                    except IndexError:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Пропущена некорректная строка (недостаточно столбцов): {row}"
                            )
                        )
                        skipped_count += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Ошибка при обработке строки {row}: {e}")
                        )
                        skipped_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Загрузка завершена. Добавлено новых ингредиентов: {loaded_count}"
                )
            )
            if skipped_count > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"Пропущено (уже существуют или ошибки): {skipped_count}"
                    )
                )
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Файл не найден: {file_path}"))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Произошла ошибка при чтении файла: {e}")
            )
