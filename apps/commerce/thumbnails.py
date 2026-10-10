"""Уменьшенные превью товаров (webp) для быстрой загрузки каталога."""
from __future__ import annotations

import logging
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

THUMBNAIL_SIZE = 400
THUMBNAIL_QUALITY = 80


def build_webp_thumbnail(image_field) -> ContentFile | None:
    if not image_field or not image_field.name:
        return None
    try:
        image_field.open('rb')
        with Image.open(image_field) as img:
            img = ImageOps.exif_transpose(img)
            img = img.convert('RGBA') if img.mode in ('P', 'LA', 'RGBA') else img.convert('RGB')
            img.thumbnail((THUMBNAIL_SIZE, THUMBNAIL_SIZE), Image.LANCZOS)
            buf = BytesIO()
            img.save(buf, format='WEBP', quality=THUMBNAIL_QUALITY, method=4)
    except (OSError, ValueError) as exc:
        logger.warning('Не удалось создать превью для %s: %s', image_field.name, exc)
        return None
    finally:
        try:
            image_field.close()
        except (OSError, ValueError):
            pass
    return ContentFile(buf.getvalue())
