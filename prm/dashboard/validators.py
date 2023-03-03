from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_image_size(image, max_size: int = 100000):
    if image.size > max_size:
        raise ValidationError(_(f"The maximum image size is {int(max_size / 1000)}kb"))


def validate_image_min_pixel_size(image, min_width: int = 100, min_height: int = 100):
    width, height = image.image.size
    if width < min_width or height < min_height:
        raise ValidationError(
            _(f"The minimum pixel size is {min_width} x {min_height}."),
            code="invalid_pixel_size",
        )


def validate_image_max_pixel_size(image, max_width: int = 1000, max_height: int = 1000):
    width, height = image.image.size
    if width > max_width or height > max_height:
        raise ValidationError(
            _(f"The maximum pixel size is {max_width} x {max_height}."),
            code="invalid_pixel_size",
        )
