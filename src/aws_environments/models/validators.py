from django.core.validators import URLValidator


class OptionalSchemeURLValidator(URLValidator):
    def __call__(self, value):
        if "://" not in value:
            value = "http://" + value
        super().__call__(value)
