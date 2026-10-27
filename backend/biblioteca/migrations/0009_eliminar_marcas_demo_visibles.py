import re

from django.db import migrations


def _sin_marca_demo(valor):
    """Conserva el dato de negocio y retira etiquetas temporales de prueba."""
    valor = re.sub(
        r'(?i)\bdemo(?:\s+\d+(?:\.\d+)*)?\s*[-:]?\s*',
        '',
        valor,
    )
    valor = re.sub(r'\(\s*\)', '', valor)
    return re.sub(r'\s{2,}', ' ', valor).strip(' -')


def eliminar_marcas_demo(apps, schema_editor):
    for modelo, campo in (
        (apps.get_model('biblioteca', 'Usuario'), 'nombre'),
        (apps.get_model('biblioteca', 'Libro'), 'titulo'),
        (apps.get_model('biblioteca', 'Autor'), 'nombre'),
    ):
        for registro in modelo.objects.filter(**{f'{campo}__icontains': 'demo'}):
            valor_original = getattr(registro, campo)
            valor_limpio = _sin_marca_demo(valor_original)
            if valor_limpio and valor_limpio != valor_original:
                setattr(registro, campo, valor_limpio)
                registro.save(update_fields=[campo])


class Migration(migrations.Migration):

    dependencies = [
        ('biblioteca', '0008_alter_categoria_nombre_categoria'),
    ]

    operations = [
        migrations.RunPython(eliminar_marcas_demo, migrations.RunPython.noop),
    ]
