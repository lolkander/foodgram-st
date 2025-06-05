import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            try:
                (format, imgstr) = data.split(";base64,")
                ext = format.split("/")[-1]
                file_name = f"{uuid.uuid4()}.{ext}"
                data = ContentFile(base64.b64decode(imgstr), name=file_name)
            except Exception as e:
                raise serializers.ValidationError(
                    "Некорректный формат base64 изображения."
                )
        return super().to_internal_value(data)

    def to_representation(self, value):
        if not value:
            return None
        request = self.context.get("request")
        if request:
            host = request.get_host()
            scheme = request.scheme
            port = request.get_port()
            if ":" not in host and port not in ("80", "443"):
                host_with_port = f"{host}:{port}"
            else:
                host_with_port = host
            image_url = value.url
            if not image_url.startswith("/"):
                image_url = f"/{image_url}"
            return f"{scheme}://{host_with_port}{image_url}"
        if hasattr(value, "url"):
            return value.url
        return None
