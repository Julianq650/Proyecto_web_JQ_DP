import datetime
import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ConfirmarReservaForm, IngresoForm, RegistroForm, ResenaForm
from .middleware import registrar
from .models import Cancha, Reserva
from .permisos import puede_recepcion
from .servicios import ahora, estado_actual, hora12, proximo_libre, turnos

ANTICIPACION_CANCELAR = datetime.timedelta(hours=2)


def mapa(request):
    canchas = []
    conteo = {'uso': 0, 'reservada': 0, 'libre': 0, 'fuera': 0}
    for c in Cancha.objects.all():
        e = estado_actual(c)
        conteo[e['estado']] += 1
        canchas.append({'obj': c, 'estado': e['estado'], 'texto': e['texto'], 'proximo': proximo_libre(c)})
    datos_mapa = [{'id': x['obj'].id, 'nombre': x['obj'].nombre, 'deporte': x['obj'].deporte, 'estado': x['estado'],
                   'texto': x['texto'], 'x': x['obj'].pos_x, 'y': x['obj'].pos_y, 'ancho': x['obj'].ancho,
                   'url': f"/canchas/{x['obj'].id}/"} for x in canchas]
    zonas = [(nombre, [x for x in canchas if x['obj'].zona == clave]) for clave, nombre in Cancha.ZONAS]
    return render(request, 'modulo/mapa.html', {'zonas': zonas, 'datos_mapa': datos_mapa, 'conteo': conteo})


def _dias(desde, n=7):
    nombres = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    return [{'fecha': desde + datetime.timedelta(d),
             'nombre': 'Hoy' if d == 0 else f'{nombres[(desde + datetime.timedelta(d)).weekday()]} {(desde + datetime.timedelta(d)).day}'}
            for d in range(n)]


def detalle(request, cancha_id):
    cancha = get_object_or_404(Cancha, pk=cancha_id)
    hoy = ahora().date()
    try:
        fecha = datetime.date.fromisoformat(request.GET.get('fecha', ''))
    except ValueError:
        fecha = hoy
    fecha = min(max(fecha, hoy), hoy + datetime.timedelta(days=6))

    e = estado_actual(cancha)
    progreso = None
    if e['estado'] == 'uso':
        total = (e['fin'] - e['inicio']).total_seconds()
        progreso = {'pct': int((ahora() - e['inicio']).total_seconds() / total * 100),
                    'faltan': int((e['fin'] - ahora()).total_seconds() // 60)}

    resenas = cancha.resenas.filter(visible=True)
    resumen = resenas.aggregate(promedio=Avg('calificacion'), total=Count('id'))
    reserva = e['reserva']
    ve_todo = reserva and (puede_recepcion(request.user) or reserva.cliente_id == request.user.id)
    return render(request, 'modulo/detalle.html', {
        'cancha': cancha, 'e': e, 'reserva': reserva, 've_todo': ve_todo, 'progreso': progreso,
        'turnos': turnos(cancha, fecha), 'fecha': fecha, 'dias': _dias(hoy),
        'actividades': cancha.actividades.filter(fecha__gte=hoy)[:3],
        'resenas': resenas[:3], 'resumen': resumen, 'form_resena': ResenaForm(),
        'otras': Cancha.objects.filter(zona=cancha.zona).exclude(pk=cancha.pk),
        'proximo': proximo_libre(cancha),
    })


@login_required
def reservar(request, cancha_id):
    cancha = get_object_or_404(Cancha, pk=cancha_id)
    try:
        fecha = datetime.date.fromisoformat(request.GET.get('fecha') or request.POST.get('fecha'))
        hora = datetime.time.fromisoformat(request.GET.get('hora') or request.POST.get('hora'))
    except (TypeError, ValueError):
        messages.error(request, 'Turno no válido.')
        return redirect('detalle', cancha_id=cancha.id)

    inicio = timezone.make_aware(datetime.datetime.combine(fecha, hora))
    if cancha.fuera_de_servicio or inicio + datetime.timedelta(hours=1) <= ahora() or fecha > ahora().date() + datetime.timedelta(days=6):
        messages.error(request, 'Ese turno ya no se puede reservar.')
        return redirect('detalle', cancha_id=cancha.id)

    valor = cancha.precio_para(fecha, hora)
    form = ConfirmarReservaForm(request.POST or None, cancha=cancha)
    if request.method == 'POST' and form.is_valid():
        nombre = request.user.get_full_name() or request.user.username
        try:
            r = Reserva.objects.create(cancha=cancha, fecha=fecha, hora_inicio=hora, cliente=request.user,
                                       nombre_cliente=nombre, telefono=form.cleaned_data['telefono'],
                                       jugadores=form.cleaned_data['jugadores'], valor=valor,
                                       medio_pago=form.cleaned_data['medio_pago'], creada_por=request.user)
        except IntegrityError:
            messages.error(request, 'Alguien acaba de reservar ese turno. Elige otro.')
            return redirect(f'/canchas/{cancha.id}/?fecha={fecha.isoformat()}')
        registrar(request, logging.INFO, 'Reserva creada por el cliente', cancha=cancha.nombre, reserva=r.codigo, valor=valor, medio_pago=r.medio_pago)
        messages.success(request, f'Reserva confirmada: {cancha.nombre}, {hora12(hora)}. Código {r.codigo}.')
        return redirect('mis_reservas')
    return render(request, 'modulo/confirmar.html', {'cancha': cancha, 'fecha': fecha, 'hora': hora, 'valor': valor, 'form': form})


@login_required
def mis_reservas(request):
    hoy = ahora().date()
    reservas = request.user.reservas.select_related('cancha')
    return render(request, 'modulo/mis_reservas.html', {
        'proximas': reservas.filter(fecha__gte=hoy).exclude(estado__in=['cancelada', 'finalizada']),
        'historial': reservas.exclude(fecha__gte=hoy, estado__in=['reservada', 'en_uso']).order_by('-fecha', '-hora_inicio')[:15],
    })


@login_required
@require_POST
def cancelar_mi_reserva(request, reserva_id):
    r = get_object_or_404(Reserva, pk=reserva_id, cliente=request.user, estado='reservada')
    inicio = timezone.make_aware(datetime.datetime.combine(r.fecha, r.hora_inicio))
    if inicio - ahora() < ANTICIPACION_CANCELAR:
        messages.error(request, 'Solo puedes cancelar hasta 2 horas antes. Comunícate con recepción.')
    else:
        r.estado = 'cancelada'
        r.save(update_fields=['estado'])
        registrar(request, logging.INFO, 'Reserva cancelada por el cliente', cancha=r.cancha.nombre, reserva=r.codigo)
        messages.success(request, f'Reserva {r.codigo} cancelada.')
    return redirect('mis_reservas')


@login_required
@require_POST
def opinar(request, cancha_id):
    cancha = get_object_or_404(Cancha, pk=cancha_id)
    form = ResenaForm(request.POST)
    if form.is_valid():
        resena = form.save(commit=False)
        resena.cancha, resena.usuario = cancha, request.user
        resena.save()
        messages.success(request, 'Gracias por tu reseña.')
    return redirect('detalle', cancha_id=cancha.id)


def ingresar(request):
    form = IngresoForm(request.POST or None)
    status, error = 200, None
    if request.method == 'POST' and form.is_valid():
        nombre = form.cleaned_data['usuario']
        usuario = authenticate(request, username=nombre, password=form.cleaned_data['clave'])
        if usuario is not None:
            login(request, usuario)
            registrar(request, logging.INFO, 'Inicio de sesión exitoso')
            return redirect(request.GET.get('next') or 'mapa')
        registrar(request, logging.WARNING, 'Intento de inicio de sesión fallido', user_id=nombre)
        error, status = 'Usuario o contraseña incorrectos.', 401
    return render(request, 'modulo/login.html', {'form': form, 'error': error}, status=status)


def registro(request):
    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        login(request, usuario)
        registrar(request, logging.INFO, 'Nuevo cliente registrado')
        return redirect('mapa')
    return render(request, 'modulo/registro.html', {'form': form})


@require_POST
def salir(request):
    logout(request)
    return redirect('mapa')
