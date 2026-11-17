import datetime
import secrets

from django.conf import settings
from django.db import models
from django.db.models import Q


class Cancha(models.Model):
    DEPORTES = [
        ('futbol5', 'Fútbol 5'), ('futbol8', 'Fútbol 8'), ('baloncesto', 'Baloncesto'),
        ('voleibol', 'Voleibol'), ('tenis', 'Tenis'), ('padel', 'Pádel'),
    ]
    ZONAS = [('futbol', 'Zona de fútbol'), ('coliseo', 'Coliseo cubierto'), ('raqueta', 'Zona de raqueta')]

    nombre = models.CharField(max_length=60)
    deporte = models.CharField(max_length=20, choices=DEPORTES)
    zona = models.CharField(max_length=20, choices=ZONAS)
    superficie = models.CharField(max_length=60)
    dimensiones = models.CharField(max_length=30)
    capacidad = models.PositiveIntegerField(help_text='Número máximo de personas')
    iluminacion = models.CharField(max_length=60, default='LED nocturna')
    incluye = models.CharField(max_length=150, blank=True)
    precio_dia = models.PositiveIntegerField('Precio entre semana (6 a. m. – 6 p. m.)')
    precio_noche = models.PositiveIntegerField('Precio entre semana (6 p. m. – 11 p. m.)')
    precio_finde = models.PositiveIntegerField('Precio sábados y domingos')
    fuera_de_servicio = models.BooleanField(default=False)
    # Posición en el mapa (coordenadas del plano de 1200 × 800)
    pos_x = models.PositiveIntegerField(default=0)
    pos_y = models.PositiveIntegerField(default=0)
    ancho = models.PositiveIntegerField(default=200)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return self.nombre

    def precio_para(self, fecha, hora):
        if fecha.weekday() >= 5:
            return self.precio_finde
        return self.precio_noche if hora.hour >= 18 else self.precio_dia


def nuevo_codigo():
    return 'RES-' + secrets.token_hex(3).upper()


class Reserva(models.Model):
    ESTADOS = [('reservada', 'Reservada'), ('en_uso', 'En uso'), ('finalizada', 'Finalizada'), ('cancelada', 'Cancelada')]
    MEDIOS = [('efectivo', 'Efectivo'), ('nequi', 'Nequi'), ('daviplata', 'Daviplata'),
              ('tarjeta', 'Tarjeta débito / crédito'), ('pse', 'PSE')]

    codigo = models.CharField(max_length=12, unique=True, default=nuevo_codigo)
    cancha = models.ForeignKey(Cancha, on_delete=models.PROTECT, related_name='reservas')
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='reservas')
    nombre_cliente = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True)
    jugadores = models.PositiveIntegerField(default=1)
    estado = models.CharField(max_length=12, choices=ESTADOS, default='reservada')
    valor = models.PositiveIntegerField()
    medio_pago = models.CharField(max_length=12, choices=MEDIOS, default='efectivo')
    pagado = models.BooleanField(default=False)
    pagado_en = models.DateTimeField(null=True, blank=True)
    llegada_en = models.DateTimeField(null=True, blank=True)
    creada_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='reservas_creadas')
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha', 'hora_inicio']
        constraints = [
            models.UniqueConstraint(fields=['cancha', 'fecha', 'hora_inicio'], condition=~Q(estado='cancelada'),
                                    name='un_turno_activo_por_cancha'),
        ]

    def __str__(self):
        return f'{self.codigo} · {self.cancha} · {self.fecha} {self.hora_inicio:%H:%M}'

    @property
    def hora_fin(self):
        return (datetime.datetime.combine(self.fecha, self.hora_inicio) + datetime.timedelta(hours=1)).time()

    @property
    def nombre_publico(self):
        """Nombre abreviado para mostrar a otros usuarios (protege la identidad)."""
        partes = self.nombre_cliente.split()
        return ' '.join(p[0] + '.' for p in partes[:2]) if partes else 'Cliente'


class Actividad(models.Model):
    cancha = models.ForeignKey(Cancha, on_delete=models.CASCADE, related_name='actividades')
    titulo = models.CharField(max_length=100)
    fecha = models.DateField()
    detalle = models.CharField(max_length=150)

    class Meta:
        ordering = ['fecha']
        verbose_name_plural = 'actividades'

    def __str__(self):
        return self.titulo


class Resena(models.Model):
    cancha = models.ForeignKey(Cancha, on_delete=models.CASCADE, related_name='resenas')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    calificacion = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comentario = models.CharField(max_length=300)
    creada_en = models.DateTimeField(auto_now_add=True)
    visible = models.BooleanField(default=True)

    class Meta:
        ordering = ['-creada_en']
        verbose_name = 'reseña'

    def __str__(self):
        return f'{self.cancha} · {self.calificacion}★'


class Incidencia(models.Model):
    cancha = models.ForeignKey(Cancha, on_delete=models.CASCADE, related_name='incidencias')
    descripcion = models.CharField(max_length=300)
    reportada_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+')
    reportada_en = models.DateTimeField(auto_now_add=True)
    resuelta = models.BooleanField(default=False)
    resuelta_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    resuelta_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['resuelta', '-reportada_en']

    def __str__(self):
        return f'{self.cancha}: {self.descripcion[:40]}'
