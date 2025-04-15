# escala/migrations/000X_populate_valor_turno.py
from django.db import migrations
from decimal import Decimal

# Valores iniciais baseados no seu código original
INITIAL_VALORES = {
    "D": Decimal("125.00"),
    "N": Decimal("125.00"),
    "I": Decimal("250.00"),
    "M": Decimal("62.50"),
    "T": Decimal("62.50"),
    "A": Decimal("62.50"),
}


def populate_valores(apps, schema_editor):
    ValorTurno = apps.get_model("escala", "ValorTurno")
    # Não precisamos do TurnoEscolha aqui, apenas os códigos

    for codigo, valor in INITIAL_VALORES.items():
        # Cria ou atualiza a entrada para cada código de turno
        ValorTurno.objects.update_or_create(
            turno_codigo=codigo, defaults={"valor": valor, "descricao": "Valor inicial"}
        )


def reverse_populate(apps, schema_editor):
    # Define como reverter: apaga as entradas criadas
    ValorTurno = apps.get_model("escala", "ValorTurno")
    ValorTurno.objects.filter(turno_codigo__in=INITIAL_VALORES.keys()).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("escala", "0007_valorturno"),
    ]

    operations = [
        migrations.RunPython(populate_valores, reverse_code=reverse_populate),
    ]
