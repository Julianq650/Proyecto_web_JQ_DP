from django.db import migrations

CANCHAS = [
    # nombre, deporte, zona, superficie, dimensiones, capacidad, incluye, día, noche, finde, x, y, ancho
    ('Fútbol 5 · Cancha 1', 'futbol5', 'futbol', 'Grama sintética', '40 × 20 m', 10, 'Balón y petos', 70000, 90000, 95000, 178, 78, 210),
    ('Fútbol 5 · Cancha 2', 'futbol5', 'futbol', 'Grama sintética', '40 × 20 m', 10, 'Balón y petos', 70000, 90000, 95000, 428, 78, 210),
    ('Fútbol 8', 'futbol8', 'futbol', 'Grama sintética', '60 × 35 m', 16, 'Balón y petos', 110000, 140000, 150000, 700, 66, 228),
    ('Baloncesto', 'baloncesto', 'coliseo', 'Madera', '28 × 15 m', 10, 'Balón', 55000, 70000, 75000, 84, 368, 222),
    ('Voleibol', 'voleibol', 'coliseo', 'Sintética', '18 × 9 m', 12, 'Balón', 45000, 60000, 65000, 326, 388, 140),
    ('Tenis · Cancha 1', 'tenis', 'raqueta', 'Arcilla', '23,8 × 11 m', 4, 'Préstamo de raquetas', 45000, 55000, 60000, 752, 318, 200),
    ('Tenis · Cancha 2', 'tenis', 'raqueta', 'Cemento', '23,8 × 11 m', 4, 'Préstamo de raquetas', 40000, 50000, 55000, 752, 462, 200),
    ('Pádel', 'padel', 'raqueta', 'Césped y vidrio', '20 × 10 m', 4, 'Préstamo de palas', 50000, 65000, 70000, 982, 330, 150),
]


def crear(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='Recepcionistas')
    Cancha = apps.get_model('modulo', 'Cancha')
    for i, (nom, dep, zona, sup, dim, cap, inc, pd, pn, pf, x, y, w) in enumerate(CANCHAS):
        Cancha.objects.get_or_create(nombre=nom, defaults=dict(
            deporte=dep, zona=zona, superficie=sup, dimensiones=dim, capacidad=cap, incluye=inc,
            precio_dia=pd, precio_noche=pn, precio_finde=pf, pos_x=x, pos_y=y, ancho=w, orden=i))


class Migration(migrations.Migration):
    dependencies = [('modulo', '0001_initial'), ('auth', '0012_alter_user_first_name_max_length')]
    operations = [migrations.RunPython(crear, migrations.RunPython.noop)]
