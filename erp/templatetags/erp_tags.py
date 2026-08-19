from django import template
from django.utils.formats import number_format

register = template.Library()


@register.filter
def widget_span(field):
    """Return the data-span value from a BoundField's widget attrs, defaulting to 'span-1'."""
    try:
        return field.field.widget.attrs.get("data-span", "span-1")
    except AttributeError:
        return "span-1"


@register.filter
def number_id(value):
    """Format angka dengan pemisah ribuan sesuai lokal Indonesia."""
    if value in (None, ""):
        value = 0
    try:
        return number_format(value, decimal_pos=0, use_l10n=True, force_grouping=True)
    except (TypeError, ValueError):
        return value
