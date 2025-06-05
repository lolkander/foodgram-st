# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app/backend/

# Устанавливаем зависимости
# Копируем сначала requirements.txt, чтобы использовать кэш Docker при изменениях кода, но не зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта в рабочую директорию
COPY . .

# (Опционально, если есть статика Django, которую нужно собрать на этапе сборки)
# RUN python manage.py collectstatic --noinput

# Открываем порт, на котором будет работать Gunicorn (этот порт используется внутри Docker-сети)
# Gunicorn будет запущен на порту 8000 внутри контейнера
EXPOSE 8000

# Команда для запуска Gunicorn
# Проверьте, что 'foodgram.wsgi:application' - это правильный путь к вашему WSGI-приложению
# (foodgram - это имя папки вашего Django-проекта, где находится wsgi.py)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi:application"] 