"""
Image processing utilities — WebP conversion and resize.

Usage in model save():
    from apps.core.images import convert_to_webp

    result = convert_to_webp(self.image)
    if result:
        new_name, content = result
        self.image.save(new_name, content, save=False)
    super().save(*args, **kwargs)
"""
import logging
import warnings
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

MAX_DIMENSION = 1600  # px — longest side capped here
WEBP_QUALITY = 82     # 82 is near-lossless for photos, ~10× smaller than raw PNG
MAX_IMAGE_PIXELS = 12_000_000
# Bound decoded memory before EXIF transforms/resize load a whole input image.
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
warnings.filterwarnings("error", category=Image.DecompressionBombWarning)


def convert_to_webp(image_field):
    """
    Read image_field, resize to MAX_DIMENSION, re-encode as WebP.

    Returns (new_name: str, content: ContentFile) ready for field.save(),
    or None if the field is empty or already a .webp.
    """
    if not image_field:
        return None
    try:
        name = image_field.name or ""
    except Exception:
        return None

    if name.lower().endswith(".webp"):
        return None

    try:
        image_field.seek(0)
        img = Image.open(image_field)
        if img.width * img.height > MAX_IMAGE_PIXELS:
            raise ValidationError("Please upload an image no larger than 12 megapixels.")
        img = ImageOps.exif_transpose(img)  # respect EXIF orientation

        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
        elif img.mode == "RGBA":
            # WebP supports RGBA — keep transparency
            pass

        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

        buf = BytesIO()
        img.save(buf, format="WEBP", quality=WEBP_QUALITY, method=6)
        buf.seek(0)

        new_name = str(Path(name).with_suffix(".webp"))
        return new_name, ContentFile(buf.getvalue())
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValidationError("Please upload an image no larger than 12 megapixels.") from exc
    except ValidationError:
        raise
    except Exception:
        logger.exception("convert_to_webp failed for %s — keeping original", name)
        return None
