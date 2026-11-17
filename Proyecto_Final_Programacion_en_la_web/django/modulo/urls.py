from django.urls import path

from . import administracion, monitor, recepcion, views

urlpatterns = [
    path('', views.mapa, name='mapa'),
    path('canchas/<int:cancha_id>/', views.detalle, name='detalle'),
    path('canchas/<int:cancha_id>/reservar/', views.reservar, name='reservar'),
    path('canchas/<int:cancha_id>/opinar/', views.opinar, name='opinar'),
    path('mis-reservas/', views.mis_reservas, name='mis_reservas'),
    path('mis-reservas/<int:reserva_id>/cancelar/', views.cancelar_mi_reserva, name='cancelar_mi_reserva'),
    path('login/', views.ingresar, name='login'),
    path('registro/', views.registro, name='registro'),
    path('salir/', views.salir, name='salir'),

    # Recepción (recepcionista y administrador)
    path('recepcion/', recepcion.agenda, name='agenda'),
    path('recepcion/nueva/', recepcion.nueva_reserva, name='nueva_reserva'),
    path('recepcion/reserva/<int:reserva_id>/<str:accion>/', recepcion.accion_reserva, name='accion_reserva'),
    path('recepcion/incidencia/', recepcion.reportar_incidencia, name='reportar_incidencia'),

    # Administración (solo administrador)
    path('administracion/', administracion.panel, name='panel'),
    path('administracion/precios/<int:cancha_id>/', administracion.guardar_precios, name='guardar_precios'),
    path('administracion/incidencia/<int:incidencia_id>/resolver/', administracion.resolver_incidencia, name='resolver_incidencia'),
    path('administracion/reserva/<int:reserva_id>/cancelar/', administracion.cancelar_pagada, name='cancelar_pagada'),
    path('administracion/resena/<int:resena_id>/', administracion.ocultar_resena, name='ocultar_resena'),
    path('administracion/usuarios/', administracion.usuarios, name='usuarios'),
    path('administracion/monitor/', monitor.monitor, name='monitor'),
    path('administracion/monitor/datos/', monitor.monitor_datos, name='monitor_datos'),
]
