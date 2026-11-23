from django.core.exceptions import ValidationError


def validate_duration(value):
    if value > 1440:
        raise ValidationError(
            "Продолжительность не должна превышать 24 часа.",
            code="duration_too_long")
