from django.core.validators import FileExtensionValidator

MANUFACTURER_LOGO_EXTENSIONS = ('jpg', 'jpeg', 'png', 'webp', 'gif', 'svg')

validate_manufacturer_logo = FileExtensionValidator(
    allowed_extensions=MANUFACTURER_LOGO_EXTENSIONS,
    message='Допустимые форматы: %(allowed_extensions)s.',
)
