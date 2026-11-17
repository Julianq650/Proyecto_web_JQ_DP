from django import template

from ..servicios import hora12 as _hora12

register = template.Library()


@register.filter
def hora12(valor):
    return _hora12(valor) if valor else ''


@register.filter
def pesos(valor):
    try:
        return '$' + f'{int(valor):,}'.replace(',', '.')
    except (TypeError, ValueError):
        return valor


@register.filter
def estrellas(valor):
    n = round(valor or 0)
    return '★' * n + '☆' * (5 - n)
