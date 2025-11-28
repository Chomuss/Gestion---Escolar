from typing import Dict, List, Optional

from django.core.exceptions import ValidationError

from academico.models import (
    Curso,
    BloqueHorario,
    HorarioCurso,
    Sala,
)
from django.conf import settings

User = settings.AUTH_USER_MODEL


def verificar_disponibilidad_sala(
    sala: Sala,
    bloque: BloqueHorario,
    periodo,
    excluir_horario_id: Optional[int] = None,
) -> bool:
    """
    Verifica si una sala está disponible en un bloque y período dados.
    Retorna True si está libre, False si ya está asignada.
    """
    qs = HorarioCurso.objects.filter(
        periodo=periodo,
        bloque=bloque,
        sala=sala,
    )
    if excluir_horario_id:
        qs = qs.exclude(id=excluir_horario_id)
    return not qs.exists()


def verificar_disponibilidad_docente(
    docente,
    bloque: BloqueHorario,
    periodo,
    excluir_horario_id: Optional[int] = None,
) -> bool:
    """
    Verifica si un docente está disponible en un bloque y período dados.
    Retorna True si está libre, False si ya tiene una clase asignada.
    """
    qs = HorarioCurso.objects.filter(
        periodo=periodo,
        bloque=bloque,
        docente=docente,
    )
    if excluir_horario_id:
        qs = qs.exclude(id=excluir_horario_id)
    return not qs.exists()


def obtener_conflictos_horario(horario: HorarioCurso) -> Dict[str, List[HorarioCurso]]:
    """
    Detecta conflictos de un HorarioCurso con otros registros.

    Conflictos considerados:
      - Conflicto de sala: misma sala + mismo bloque + mismo periodo.
      - Conflicto de docente: mismo docente + mismo bloque + mismo periodo.
      - Conflicto de curso: mismo curso + mismo bloque + mismo periodo
        (doble clase en mismo bloque).

    Retorna un dict con listas de objetos conflictivos.
    """
    conflictos = {
        "sala": [],
        "docente": [],
        "curso": [],
    }

    qs_base = HorarioCurso.objects.filter(
        periodo=horario.periodo,
        bloque=horario.bloque,
    ).exclude(id=horario.id)

    if horario.sala:
        conflictos["sala"] = list(
            qs_base.filter(sala=horario.sala)
        )

    if horario.docente:
        conflictos["docente"] = list(
            qs_base.filter(docente=horario.docente)
        )

    conflictos["curso"] = list(
        qs_base.filter(curso=horario.curso)
    )

    return conflictos


def validar_horario_sin_conflictos(horario: HorarioCurso) -> None:
    """
    Valida que un horario no tenga conflictos de sala, docente o curso.
    Lanza ValidationError con mensajes agregados si encuentra alguno.
    """
    conflictos = obtener_conflictos_horario(horario)
    errores = []

    if conflictos["sala"]:
        errores.append(
            f"La sala {horario.sala} ya tiene clases en el bloque {horario.bloque}."
        )

    if conflictos["docente"]:
        errores.append(
            f"El docente {horario.docente} ya tiene clases en el bloque {horario.bloque}."
        )

    if conflictos["curso"]:
        errores.append(
            f"El curso {horario.curso} ya tiene otra clase en el bloque {horario.bloque}."
        )

    if errores:
        raise ValidationError({"detalle_conflictos": errores})


def crear_horario_curso(
    curso: Curso,
    asignatura,
    docente,
    sala: Optional[Sala],
    bloque: BloqueHorario,
    periodo,
    es_rotativo: bool = False,
    validar_conflictos: bool = True,
) -> HorarioCurso:
    """
    Crea un HorarioCurso aplicando las validaciones de disponibilidad.

    Se recomienda usar esta función desde views, comandos o tareas para
    centralizar la lógica de negocio de creación de horarios.
    """
    horario = HorarioCurso(
        curso=curso,
        asignatura=asignatura,
        docente=docente,
        sala=sala,
        bloque=bloque,
        periodo=periodo,
        es_rotativo=es_rotativo,
    )

    if validar_conflictos:
        validar_horario_sin_conflictos(horario)

    horario.full_clean()
    horario.save()
    return horario


def duplicar_horario_como_rotativo(
    horario: HorarioCurso,
    nuevo_bloque: BloqueHorario,
) -> HorarioCurso:
    """
    Crea una copia de un horario existente marcándolo como rotativo,
    en un nuevo bloque horario.

    Útil para manejar horarios especiales o rotaciones semestrales.
    """
    nuevo = HorarioCurso(
        curso=horario.curso,
        asignatura=horario.asignatura,
        docente=horario.docente,
        sala=horario.sala,
        bloque=nuevo_bloque,
        periodo=horario.periodo,
        es_rotativo=True,
    )

    validar_horario_sin_conflictos(nuevo)
    nuevo.full_clean()
    nuevo.save()
    return nuevo
