from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

GRUPO_RECEPCION = 'Recepcionistas'


def es_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)


def es_recepcionista(user):
    return user.is_authenticated and user.groups.filter(name=GRUPO_RECEPCION).exists()


def puede_recepcion(user):
    """El administrador también puede usar todas las funciones de recepción."""
    return es_admin(user) or es_recepcionista(user)


def rol(user):
    if es_admin(user):
        return 'administrador'
    if es_recepcionista(user):
        return 'recepcionista'
    return 'cliente' if user.is_authenticated else 'visitante'


def _requiere(prueba):
    def decorador(vista):
        @login_required
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if not prueba(request.user):
                raise PermissionDenied
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador


solo_recepcion = _requiere(puede_recepcion)
solo_admin = _requiere(es_admin)


def contexto(request):
    """Disponible en todas las plantillas para mostrar el menú según el rol."""
    return {'rol_usuario': rol(request.user), 'puede_recepcion': puede_recepcion(request.user),
            'es_admin': es_admin(request.user)}
