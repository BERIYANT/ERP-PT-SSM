from django import template

register = template.Library()


@register.filter
def widget_span(field):
    """Return the data-span value from a BoundField's widget attrs, defaulting to 'span-1'."""
    try:
        return field.field.widget.attrs.get("data-span", "span-1")
    except AttributeError:
        return "span-1"
