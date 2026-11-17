"""Funciones del recepcionista: operación diaria del complejo."""
import datetime
import logging

from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import IncidenciaForm, ReservaPresencialForm
from .middleware import registrar
from .models import Cancha, Incidencia, Reserva
from .permisos import solo_recepcion
from .servicios import ahora, estado_actual, horas_del_dia


@solo_recepcion
def agenda(request):
    hoy = ahora().date()
    canchas = list(Cancha.objects.all())
    reservas = Reserva.objects.filter(fecha=hoy).exclude(estado='cancelada').select_related('cancha')
    por_celda = {(r.cancha_id, r.hora_inicio): r for r in reservas}
    filas = [{'cancha': c, 'estado': estado_actual(c),
              'celdas': [por_celda.get((c.id, h)) for h in horas_del_dia()]} for c in canchas]

    pagadas_hoy = Reserva.objects.filter(pagado=True, pagado_en__date=hoy)
    caja = pagadas_hoy.values('medio_pago').annotate(total=Sum('valor'), n=Count('id')).order_by('-total')
    medios = dict(Reserva.MEDIOS)
    return render(request, 'modulo/recepcion/agenda.html', {
        'filas': filas, 'horas': horas_del_dia(), 'hora_actual': ahora().hour,
        'reservas': reservas.order_by('hora_inicio', 'cancha__orden'),
        'caja': [{'medio': medios[c['medio_pago']], 'total': c['total'], 'n': c['n']} for c in caja],
        'total_caja': pagadas_hoy.aggregate(t=Sum('valor'))['t'] or 0,
        'pendientes': reservas.filter(pagado=False).count(),
        'medios': Reserva.MEDIOS,
        'incidencias': Incidencia.objects.filter(resuelta=False).select_related('cancha'),
    })


@solo_recepcion
def nueva_reserva(request):
    form = ReservaPresencialForm(request.POST or None, initial={'cancha': request.GET.get('cancha'), 'hora': request.GET.get('hora')})
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        fecha = datetime.date.fromisoformat(d['fecha'])
        hora = datetime.time.fromisoformat(d['hora'])
        cancha = d['cancha']
        if timezone.make_aware(datetime.datetime.combine(fecha, hora)) + datetime.timedelta(hours=1) <= ahora():
            form.add_error('hora', 'Ese turno ya pasó.')
        elif d['jugadores'] > cancha.capacidad:
            form.add_error('jugadores', f'La capacidad máxima es {cancha.capacidad}.')
        else:
            try:
                r = Reserva.objects.create(
                    cancha=cancha, fecha=fecha, hora_inicio=hora, nombre_cliente=d['nombre_cliente'],
                    telefono=d['telefono'], jugadores=d['jugadores'], valor=cancha.precio_para(fecha, hora),
                    medio_pago=d['medio_pago'], pagado=d['pagado'], pagado_en=ahora() if d['pagado'] else None,
                    creada_por=request.user)
            except IntegrityError:
                form.add_error('hora', 'Ese turno ya está reservado.')
            else:
                registrar(request, logging.INFO, 'Reserva presencial creada', cancha=cancha.nombre, reserva=r.codigo,
                          valor=r.valor, medio_pago=r.medio_pago)
                messages.success(request, f'Reserva {r.codigo} creada para {r.nombre_cliente}.')
                return redirect('agenda')
    return render(request, 'modulo/recepcion/nueva.html', {'form': form})


@solo_recepcion
@require_POST
def accion_reserva(request, reserva_id, accion):
    r = get_object_or_404(Reserva, pk=reserva_id)
    if accion == 'llegada' and r.estado == 'reservada':
        r.estado, r.llegada_en = 'en_uso', ahora()
        r.save(update_fields=['estado', 'llegada_en'])
        registrar(request, logging.INFO, 'Llegada del cliente registrada', cancha=r.cancha.nombre, reserva=r.codigo)
        messages.success(request, f'Llegada registrada: {r.nombre_cliente}.')
    elif accion == 'pago' and not r.pagado:
        medio = request.POST.get('medio_pago', r.medio_pago)
        if medio in dict(Reserva.MEDIOS):
            r.medio_pago = medio
        r.pagado, r.pagado_en = True, ahora()
        r.save(update_fields=['pagado', 'pagado_en', 'medio_pago'])
        registrar(request, logging.INFO, 'Pago registrado', cancha=r.cancha.nombre, reserva=r.codigo, valor=r.valor, medio_pago=r.medio_pago)
        messages.success(request, f'Pago de {r.codigo} registrado.')
    elif accion == 'finalizar' and r.estado in ('reservada', 'en_uso'):
        r.estado = 'finalizada'
        r.save(update_fields=['estado'])
        registrar(request, logging.INFO, 'Turno finalizado', cancha=r.cancha.nombre, reserva=r.codigo)
    elif accion == 'cancelar' and r.estado == 'reservada' and not r.pagado and r.fecha >= ahora().date():
        # Una reserva ya pagada solo la puede cancelar el administrador (implica devolver dinero)
        r.estado = 'cancelada'
        r.save(update_fields=['estado'])
        registrar(request, logging.WARNING, 'Reserva cancelada en recepción', cancha=r.cancha.nombre, reserva=r.codigo)
        messages.success(request, f'Reserva {r.codigo} cancelada.')
    else:
        messages.error(request, 'Esa acción no está permitida para esta reserva.')
    return redirect('agenda')


@solo_recepcion
def reportar_incidencia(request):
    form = IncidenciaForm(request.POST or None, initial={'cancha': request.GET.get('cancha')})
    if request.method == 'POST' and form.is_valid():
        inc = form.save(commit=False)
        inc.reportada_por = request.user
        inc.save()
        inc.cancha.fuera_de_servicio = True
        inc.cancha.save(update_fields=['fuera_de_servicio'])
        registrar(request, logging.ERROR, 'Cancha reportada fuera de servicio', cancha=inc.cancha.nombre)
        messages.success(request, f'{inc.cancha} quedó fuera de servicio. El administrador debe revisar la novedad.')
        return redirect('agenda')
    return render(request, 'modulo/recepcion/incidencia.html', {'form': form})
