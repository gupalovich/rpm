from django.conf import settings


def allauth_settings(request):
    """Expose some settings from django-allauth in templates."""
    return {
        "ACCOUNT_ALLOW_REGISTRATION": settings.ACCOUNT_ALLOW_REGISTRATION,
    }


def htmx_settings(request):
    """Expose some settings from htmx in templates."""
    return {
        "HTMX_ALLOW_POLLING": settings.HTMX_ALLOW_POLLING,
    }
