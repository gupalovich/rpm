from django import template

register = template.Library()


@register.filter
def strip_zeros(value):
    """
    Remove trailing zeros from decimal numbers.
    """
    return str(value).rstrip("0").rstrip(".") if value else ""
