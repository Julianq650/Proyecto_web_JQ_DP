import datetime

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Cancha, Incidencia, Reserva, Resena
from .servicios import ahora, horas_del_dia, hora12


class IngresoForm(forms.Form):
    usuario = forms.CharField(max_length=150)
    clave = forms.CharField(widget=forms.PasswordInput, label='Contraseña')


class RegistroForm(UserCreationForm):
    first_name = forms.CharField(label='Nombre', max_length=60)
    last_name = forms.CharField(label='Apellido', max_length=60)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']


class ConfirmarReservaForm(forms.Form):
    jugadores = forms.IntegerField(min_value=1, initial=2)
    medio_pago = forms.ChoiceField(choices=Reserva.MEDIOS, label='Medio de pago')
    telefono = forms.CharField(max_length=20, label='Teléfono de contacto')

    def __init__(self, *args, cancha=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['jugadores'].max_value = cancha.capacidad
        self.fields['jugadores'].widget.attrs['max'] = cancha.capacidad


def _opciones_fecha(dias=7):
    hoy = ahora().date()
    nombres = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    return [((hoy + datetime.timedelta(d)).isoformat(),
             'Hoy' if d == 0 else f'{nombres[(hoy + datetime.timedelta(d)).weekday()]} {(hoy + datetime.timedelta(d)).day}')
            for d in range(dias)]


class ReservaPresencialForm(forms.Form):
    """Reserva que el recepcionista crea para un cliente que llega o llama."""
    cancha = forms.ModelChoiceField(queryset=Cancha.objects.filter(fuera_de_servicio=False))
    fecha = forms.ChoiceField()
    hora = forms.ChoiceField(choices=[(h.strftime('%H:%M'), hora12(h)) for h in horas_del_dia()])
    nombre_cliente = forms.CharField(max_length=100, label='Nombre del cliente')
    telefono = forms.CharField(max_length=20, required=False, label='Teléfono')
    jugadores = forms.IntegerField(min_value=1, initial=2)
    medio_pago = forms.ChoiceField(choices=Reserva.MEDIOS, label='Medio de pago')
    pagado = forms.BooleanField(required=False, label='El cliente ya pagó')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha'].choices = _opciones_fecha()


class IncidenciaForm(forms.ModelForm):
    class Meta:
        model = Incidencia
        fields = ['cancha', 'descripcion']
        widgets = {'descripcion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ej.: red de voleibol rota, luz fundida en la esquina norte…'})}


class ResenaForm(forms.ModelForm):
    calificacion = forms.TypedChoiceField(label='Calificación', coerce=int,
                                          choices=[('', 'Elige de 1 a 5 estrellas')] + [(i, '★' * i) for i in range(5, 0, -1)])

    class Meta:
        model = Resena
        fields = ['calificacion', 'comentario']
        widgets = {'comentario': forms.Textarea(attrs={'rows': 2})}


class PreciosForm(forms.ModelForm):
    class Meta:
        model = Cancha
        fields = ['precio_dia', 'precio_noche', 'precio_finde']
