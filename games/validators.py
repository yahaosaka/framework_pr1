from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError


def validate_game_image(value):
    if not value:
        return
    if value.size > 5 * 1024 * 1024:
        raise ValidationError("Изображение должно быть не больше 5 МБ.")
    file = getattr(value, "file", value)
    try:
        file.seek(0)
        image = Image.open(file)
        if image.format not in {"PNG", "JPEG", "WEBP"}:
            raise ValidationError("Допустимы только PNG, JPEG и WEBP.")
        if image.width * image.height > 20_000_000:
            raise ValidationError("Изображение превышает 20 мегапикселей.")
        image.verify()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValidationError(
            "Файл не является корректным изображением.") from exc
    finally:
        file.seek(0)
