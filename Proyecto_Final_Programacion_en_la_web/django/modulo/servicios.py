import datetime

from django.utils import timezone

from .models import Reserva

HORA_APERTURA, HORA_CIERRE = 6, 23          # turnos de 6:00 a. m. a 11:00 p. m.
VENTANA_RESERVADA = datetime.timedelta(minutes=120)


def ahora():
    return timezone.localtime()


def hora12(t):
    h = t.hour % 12 or 12
    sufijo = 'a. m.' if t.hour < 12 else 'p. m.'
    return f'{h}:{t.minute:02d} {sufijo}'


def horas_del_dia():
    return [datetime.time(h) for h in range(HORA_APERTURA, HORA_CIERRE)]


def estado_actual(cancha, momento=None):
    """Devuelve el estado de la cancha en este momento y el texto corto para el mapa."""
    momento = momento or ahora()
    if cancha.fuera_de_servicio:
        return {'estado': 'fuera', 'texto': 'Fuera de servicio', 'reserva': None}

    hoy = momento.date()
    activas = Reserva.objects.filter(cancha=cancha, fecha=hoy).exclude(estado__in=['cancelada', 'finalizada'])
    for r in activas:
        inicio = timezone.make_aware(datetime.datetime.combine(hoy, r.hora_inicio))
        fin = inicio + datetime.timedelta(hours=1)
        if inicio <= momento < fin:
            return {'estado': 'uso', 'texto': f'Hasta las {hora12(r.hora_fin)}', 'reserva': r,
                    'inicio': inicio, 'fin': fin}
    for r in activas:
        inicio = timezone.make_aware(datetime.datetime.combine(hoy, r.hora_inicio))
        if momento < inicio <= momento + VENTANA_RESERVADA:
            return {'estado': 'reservada', 'texto': f'Reservada · {hora12(r.hora_inicio)}', 'reserva': r,
                    'inicio': inicio}
    return {'estado': 'libre', 'texto': 'Disponible', 'reserva': None}


def turnos(cancha, fecha):
    """Lista de turnos del día con su reserva (si la hay) y si ya pasó."""
    momento = ahora()
    reservas = {r.hora_inicio: r for r in Reserva.objects.filter(cancha=cancha, fecha=fecha).exclude(estado='cancelada')}
    lista = []
    for h in horas_del_dia():
        inicio = timezone.make_aware(datetime.datetime.combine(fecha, h))
        lista.append({
            'hora': h, 'fin': (datetime.datetime.combine(fecha, h) + datetime.timedelta(hours=1)).time(),
            'reserva': reservas.get(h), 'pasado': inicio + datetime.timedelta(hours=1) <= momento,
            'precio': cancha.precio_para(fecha, h),
        })
    return lista


def proximo_libre(cancha):
    momento = ahora()
    for t in turnos(cancha, momento.date()):
        if not t['reserva'] and not t['pasado']:
            inicio = timezone.make_aware(datetime.datetime.combine(momento.date(), t['hora']))
            return 'Ahora' if inicio <= momento else hora12(t['hora'])
    return 'Mañana'
