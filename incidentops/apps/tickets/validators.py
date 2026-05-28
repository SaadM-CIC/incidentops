import os
from django.core.exceptions import ValidationError
from django.conf import settings


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    allowed = getattr(
        settings,
        'ALLOWED_UPLOAD_EXTENSIONS',
        ['.pdf', '.png', '.jpg', '.jpeg', '.txt']
    )
    if ext not in allowed:
        raise ValidationError(
            f"Extension non autorisée. Extensions acceptées : {', '.join(allowed)}"
        )


def validate_file_size(value):
    max_size = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 5 * 1024 * 1024)
    if value.size > max_size:
        raise ValidationError(
            f"Fichier trop volumineux. Taille maximale : {max_size // (1024*1024)} MB"
        )