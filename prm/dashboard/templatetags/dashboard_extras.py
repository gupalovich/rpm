import re

from django import template

register = template.Library()


@register.filter
def strip_zeros(value):
    """Remove trailing zeros from decimal numbers."""
    return str(value).rstrip("0").rstrip(".") if value else ""


@register.filter
def clean_phone_number(value):
    """Remove all non-digit characters from the phone number"""
    return re.sub(r"\D", "", value)
