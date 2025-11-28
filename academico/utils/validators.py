# academico/utils/validators.py

from decimal import Decimal
from typing import Optional

from django.core.exceptions import ValidationError

from academico.models import Curso


def validar_capacidad_curso(
    curso: Curso,
    nuevos_estudiantes: int = 0,
) -> None:
    """
    Valida que la cantidad de estudiantes en un curso no exceda
    su capacidad_maxima, considerando opcionalmente nuevos_estudiantes
    a agregar.

    Lanza ValidationError si se excede.
    """
    capacidad = curso.capacidad_maxima or 0
    actuales = curso.estudiantes.count()
    total = actuales + nuevos_estudiantes

    if capacidad > 0 and total > capacidad:
        raise ValidationError(
            f"El curso '{curso.nombre}' tiene capacidad máxima "
            f"{capacidad} y se está intentando asignar {total} estudiantes."
        )


def validar_nota_en_rango(
    nota: float,
    minimo: float = 1.0,
    maximo: float = 7.0,
) -> None:
    """
    Valida que una nota esté dentro del rango permitido.
    Lanza ValidationError si no lo está.
    """
    if nota < minimo or nota > maximo:
        raise ValidationError(
            f"La nota {nota} está fuera del rango permitido "
            f"({minimo} - {maximo})."
        )


def validar_ponderacion_total(
    ponderaciones: Optional[list[Decimal]],
    total_esperado: Decimal = Decimal("1.0"),
    tolerancia: Decimal = Decimal("0.01"),
) -> None:
    """
    Valida que la suma de un conjunto de ponderaciones sea aproximadamente
    igual a total_esperado (por defecto, 1.0 = 100%).

    Útil si en el futuro manejas ponderaciones de evaluaciones.
    """
    if not ponderaciones:
        return

    total = sum(ponderaciones)
    if not (total_esperado - tolerancia <= total <= total_esperado + tolerancia):
        raise ValidationError(
            f"La suma de las ponderaciones ({total}) no coincide con el total "
            f"esperado ({total_esperado})."
        )
