from django.contrib import admin

from .models import Actividad, Cancha, Incidencia, Reserva, Resena

admin.site.site_header = 'Multi-Dust · Administración'


@admin.register(Cancha)
class CanchaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'deporte', 'zona', 'precio_dia', 'precio_noche', 'precio_finde', 'fuera_de_servicio')
    list_editable = ('fuera_de_servicio',)
    list_filter = ('zona', 'deporte')


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'cancha', 'fecha', 'hora_inicio', 'nombre_cliente', 'estado', 'valor', 'pagado', 'medio_pago')
    list_filter = ('estado', 'pagado', 'cancha', 'fecha')
    search_fields = ('codigo', 'nombre_cliente', 'telefono')


admin.site.register(Actividad)
admin.site.register(Resena)
admin.site.register(Incidencia)
