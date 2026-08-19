from decimal import Decimal
from django import template

register = template.Library()


@register.filter
def widget_span(field):
    """Return the data-span value from a BoundField's widget attrs, defaulting to 'span-1'."""
    try:
        return field.field.widget.attrs.get("data-span", "span-1")
    except AttributeError:
        return "span-1"


@register.filter
def number_id(value, decimals=0):
    """Format angka dengan pemisah ribuan titik (.) dan desimal koma (,) sesuai lokal Indonesia."""
    if value in (None, ""):
        return "0"
    try:
        # Convert to string first to prevent float precision issues with Decimal
        val_str = str(value).strip()
        val = Decimal(val_str)
        dec = int(decimals)
        if dec == 0:
            val_int = int(round(val))
            return f"{val_int:,}".replace(",", ".")
        else:
            fmt = f"{{:,.{dec}f}}".format(val)
            parts = fmt.split(".")
            int_part = parts[0].replace(",", ".")
            dec_part = parts[1] if len(parts) > 1 else "0" * dec
            return f"{int_part},{dec_part}"
    except (TypeError, ValueError, Exception):
        return str(value)


@register.filter
def rupiah(value, decimals=0):
    """Format rupiah dengan pemisah ribuan titik."""
    return f"Rp {number_id(value, decimals)}"
