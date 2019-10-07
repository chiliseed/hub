from django.conf import settings


def get_email_context(user):
    """Return email context."""
    return dict(
        user=user,
        domain=settings.FRONT_END_DOMAIN,
        protocol="http" if settings.DEBUG else "https",
    )
