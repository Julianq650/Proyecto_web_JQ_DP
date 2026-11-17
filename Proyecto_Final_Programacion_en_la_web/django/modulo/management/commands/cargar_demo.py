"""Crea usuarios y reservas de ejemplo para ver el sistema funcionando.

Uso: python manage.py cargar_demo
Solo carga datos si todavía no hay reservas.
"""
import datetime
import random

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils import timezone

from modulo.models import Actividad, Cancha, Incidencia, Reserva, Resena

NOMBRES = ['Andrés Martínez', 'Laura Gómez', 'Camila Rojas', 'Julián Pérez', 'Valentina Díaz', 'Santiago Torres',
           'Mariana López', 'Felipe Castro', 'Daniela Ruiz', 'Sebastián Vargas', 'Torneo empresarial', 'Escuela infantil']


class Command(BaseCommand):
    help = 'Carga usuarios y reservas de demostración'

    def handle(self, *args, **opciones):
        if Reserva.objects.exists():
            self.stdout.write('Ya hay reservas; no se cargan datos de demostración.')
            return
        random.seed(42)
        grupo = Group.objects.get(name='Recepcionistas')
        recep, creado = User.objects.get_or_create(username='recepcion', defaults={'first_name': 'Sandra', 'last_name': 'Ortiz'})
        if creado:
            recep.set_password('RecepcionMultiDust2026')
            recep.save()
        recep.groups.add(grupo)
        cliente, creado = User.objects.get_or_create(username='cliente', defaults={'first_name': 'Andrés', 'last_name': 'Martínez'})
        if creado:
            cliente.set_password('ClienteMultiDust2026')
            cliente.save()

        ahora = timezone.localtime()
        hoy = ahora.date()
        canchas = list(Cancha.objects.all())
        por_nombre = {c.deporte + str(i): c for i, c in enumerate(canchas)}
        f51, f52, f8, bal, vol, te1, te2, pad = canchas

        def reservar(c, fecha, hora, nombre, usuario=None, estado='reservada', pagado=False, medio='nequi'):
            try:
                return Reserva.objects.create(
                    cancha=c, fecha=fecha, hora_inicio=datetime.time(hora), cliente=usuario, nombre_cliente=nombre,
                    telefono='300' + str(random.randint(1000000, 9999999)), jugadores=min(c.capacidad, random.randint(2, 10)),
                    valor=c.precio_para(fecha, datetime.time(hora)), estado=estado, pagado=pagado, medio_pago=medio,
                    pagado_en=timezone.make_aware(datetime.datetime.combine(fecha, datetime.time(hora))) if pagado else None,
                    creada_por=recep)
            except Exception:
                return None

        # Historial de 30 días para el panel del administrador
        for d in range(1, 30):
            fecha = hoy - datetime.timedelta(days=d)
            for c in canchas:
                for h in random.sample(range(6, 23), random.randint(3, 9)):
                    reservar(c, fecha, h, random.choice(NOMBRES), estado='finalizada', pagado=True,
                             medio=random.choice(['efectivo', 'nequi', 'daviplata', 'tarjeta', 'pse']))

        # Hoy: estados variados según la hora actual
        h = ahora.hour
        if 6 <= h < 22:
            reservar(f51, hoy, h, 'Andrés Martínez', cliente, 'en_uso', True)
            reservar(bal, hoy, h, 'Julián Pérez', estado='en_uso', pagado=True, medio='efectivo')
            reservar(pad, hoy, h, 'Camila Rojas', estado='en_uso')
            reservar(f52, hoy, h + 1, 'Laura Gómez')
            reservar(te2, hoy, h + 1, 'Valentina Díaz', pagado=True, medio='daviplata')
        for hora in range(max(6, h + 2), 23, 2):
            reservar(random.choice([f51, f52, f8, bal, te1]), hoy, hora, random.choice(NOMBRES))
        for hora in range(6, h):
            reservar(random.choice(canchas[:4]), hoy, hora, random.choice(NOMBRES), estado='finalizada', pagado=True, medio='efectivo')
        # Próximos días
        for d in range(1, 6):
            for c in canchas:
                for hora in random.sample(range(7, 23), 3):
                    reservar(c, hoy + datetime.timedelta(days=d), hora, random.choice(NOMBRES))
        reservar(te1, hoy + datetime.timedelta(days=2), 18, 'Andrés Martínez', cliente)

        vol.fuera_de_servicio = True
        vol.save()
        Incidencia.objects.create(cancha=vol, descripcion='La red está rota y uno de los postes quedó flojo.', reportada_por=recep)

        for c in canchas:
            Actividad.objects.create(cancha=c, titulo=f'Torneo relámpago de {c.get_deporte_display().lower()}',
                                     fecha=hoy + datetime.timedelta(days=7), detalle='8:00 a. m. – 2:00 p. m. · Inscripciones abiertas')
            Actividad.objects.create(cancha=c, titulo='Mantenimiento programado', fecha=hoy + datetime.timedelta(days=14),
                                     detalle='Cerrada de 6:00 a 10:00 a. m.')
        comentarios = [(5, 'Excelente estado y muy buena iluminación para jugar de noche.'),
                       (4, 'Buen precio. Sería bueno tener más turnos los fines de semana.'),
                       (5, 'La atención en recepción fue rápida y amable.')]
        for c in canchas:
            for calif, texto in comentarios:
                Resena.objects.create(cancha=c, usuario=cliente, calificacion=calif, comentario=texto)
        self.stdout.write(self.style.SUCCESS('Datos de demostración cargados.'))
