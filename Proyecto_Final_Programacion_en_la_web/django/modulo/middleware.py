import logging
import time

from .permisos import rol

logger = logging.getLogger('multidust')


def ip_cliente(request):
    reenviada = request.META.get('HTTP_X_FORWARDED_FOR')
    if reenviada:
        return reenviada.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class RegistroPeticionesMiddleware:
    """Registra cada petición con su código de respuesta y su duración."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        inicio = time.perf_counter()
        response = self.get_response(request)
        # El monitor consulta datos cada pocos segundos; no se registra para no llenar los logs de ruido
        if request.path.startswith('/administracion/monitor/datos/'):
            return response
        duracion = round((time.perf_counter() - inicio) * 1000, 2)

        if response.status_code >= 500:
            nivel = logging.ERROR
        elif response.status_code >= 400:
            nivel = logging.WARNING
        else:
            nivel = logging.INFO

        usuario = request.user.username if getattr(request, 'user', None) and request.user.is_authenticated else 'anonimo'
        logger.log(nivel, f'{request.method} {request.path} {response.status_code}', extra={
            'tipo': 'peticion',
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'response_time_ms': duracion,
            'user_id': usuario,
            'rol': rol(request.user) if hasattr(request, 'user') else 'visitante',
            'ip': ip_cliente(request),
        })
        return response


def registrar(request, nivel, mensaje, **extra):
    """Registra un evento del negocio (reserva, pago, incidencia...) en formato JSON."""
    usuario = request.user.username if request.user.is_authenticated else 'anonimo'
    datos = {'tipo': 'evento', 'user_id': usuario, 'rol': rol(request.user), 'ip': ip_cliente(request)}
    datos.update(extra)
    logger.log(nivel, mensaje, extra=datos)
