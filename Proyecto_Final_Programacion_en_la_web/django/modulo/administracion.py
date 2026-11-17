"""Funciones exclusivas del administrador: negocio, configuración y personal."""
import datetime
import logging

from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import PreciosForm
from .middleware import registrar
from .models import Cancha, Incidencia, Reserva, Resena
from .permisos import GRUPO_RECEPCION, solo_admin
from .servicios import HORA_APERTURA, HORA_CIERRE, ahora


@solo_admin
def panel(request):
    hoy = ahora().date()
    hace30 = hoy - datetime.timedelta(days=29)
    pagadas = Reserva.objects.filter(pagado=True)
    ingresos = {
        'hoy': pagadas.filter(fecha=hoy).aggregate(t=Sum('valor'))['t'] or 0,
        'semana': pagadas.filter(fecha__gte=hoy - datetime.timedelta(days=6), fecha__lte=hoy).aggregate(t=Sum('valor'))['t'] or 0,
        'mes': pagadas.filter(fecha__gte=hace30, fecha__lte=hoy).aggregate(t=Sum('valor'))['t'] or 0,
    }
    horas_posibles = (HORA_CIERRE - HORA_APERTURA) * 30
    canchas = Cancha.objects.annotate(
        horas=Count('reservas', filter=Q(reservas__fecha__gte=hace30, reservas__fecha__lte=hoy) & ~Q(reservas__estado='cancelada')),
        ingresos=Sum('reservas__valor', filter=Q(reservas__pagado=True, reservas__fecha__gte=hace30, reservas__fecha__lte=hoy)),
    )
    filas = [{'c': c, 'horas': c.horas, 'ingresos': c.ingresos or 0,
              'ocupacion': round(c.horas / horas_posibles * 100, 1), 'form': PreciosForm(instance=c, prefix=f'c{c.id}')}
             for c in canchas]
    max_ing = max([f['ingresos'] for f in filas] + [1])
    for f in filas:
        f['barra'] = int(f['ingresos'] / max_ing * 100)

    por_estado = dict(Reserva.objects.filter(fecha__gte=hace30, fecha__lte=hoy).values_list('estado').annotate(n=Count('id')))
    return render(request, 'modulo/administracion/panel.html', {
        'ingresos': ingresos, 'filas': filas, 'por_estado': por_estado,
        'total_reservas': sum(n for e, n in por_estado.items() if e != 'cancelada'),
        'incidencias': Incidencia.objects.select_related('cancha', 'reportada_por')[:10],
        'pagadas_canceladas': Reserva.objects.filter(pagado=True, estado='reservada', fecha__gte=hoy).select_related('cancha')[:8],
        'resenas': Resena.objects.select_related('cancha', 'usuario')[:6],
    })


@solo_admin
@require_POST
def guardar_precios(request, cancha_id):
    cancha = get_object_or_404(Cancha, pk=cancha_id)
    form = PreciosForm(request.POST, instance=cancha, prefix=f'c{cancha.id}')
    if form.is_valid():
        form.save()
        registrar(request, logging.INFO, 'Precios actualizados', cancha=cancha.nombre)
        messages.success(request, f'Precios de {cancha} actualizados.')
    else:
        messages.error(request, 'Revisa los valores de los precios.')
    return redirect('panel')


@solo_admin
@require_POST
def resolver_incidencia(request, incidencia_id):
    inc = get_object_or_404(Incidencia, pk=incidencia_id, resuelta=False)
    inc.resuelta, inc.resuelta_por, inc.resuelta_en = True, request.user, ahora()
    inc.save()
    if not inc.cancha.incidencias.filter(resuelta=False).exists():
        inc.cancha.fuera_de_servicio = False
        inc.cancha.save(update_fields=['fuera_de_servicio'])
    registrar(request, logging.INFO, 'Incidencia resuelta, cancha habilitada', cancha=inc.cancha.nombre)
    messages.success(request, f'{inc.cancha} vuelve a estar habilitada.')
    return redirect('panel')


@solo_admin
@require_POST
def cancelar_pagada(request, reserva_id):
    r = get_object_or_404(Reserva, pk=reserva_id, pagado=True, estado='reservada')
    r.estado = 'cancelada'
    r.save(update_fields=['estado'])
    registrar(request, logging.WARNING, 'Reserva pagada cancelada (requiere devolución)', cancha=r.cancha.nombre,
              reserva=r.codigo, valor=r.valor, medio_pago=r.medio_pago)
    messages.success(request, f'{r.codigo} cancelada. Recuerda devolver {r.valor} por {r.get_medio_pago_display()}.')
    return redirect('panel')


@solo_admin
@require_POST
def ocultar_resena(request, resena_id):
    resena = get_object_or_404(Resena, pk=resena_id)
    resena.visible = not resena.visible
    resena.save(update_fields=['visible'])
    return redirect('panel')


@solo_admin
def usuarios(request):
    grupo, _ = Group.objects.get_or_create(name=GRUPO_RECEPCION)
    if request.method == 'POST':
        u = get_object_or_404(User, pk=request.POST.get('usuario'))
        if u.is_superuser or u.is_staff:
            messages.error(request, 'Los administradores ya tienen todos los permisos.')
        elif u.groups.filter(pk=grupo.pk).exists():
            u.groups.remove(grupo)
            registrar(request, logging.WARNING, f'Rol de recepcionista retirado a {u.username}')
            messages.success(request, f'{u.username} ahora es cliente.')
        else:
            u.groups.add(grupo)
            registrar(request, logging.INFO, f'Rol de recepcionista asignado a {u.username}')
            messages.success(request, f'{u.username} ahora es recepcionista.')
        return redirect('usuarios')
    lista = User.objects.annotate(n_reservas=Count('reservas')).order_by('-is_staff', 'username')
    return render(request, 'modulo/administracion/usuarios.html', {
        'usuarios': [{'u': u, 'rol': 'Administrador' if (u.is_superuser or u.is_staff) else
                      ('Recepcionista' if u.groups.filter(pk=grupo.pk).exists() else 'Cliente')} for u in lista]})
