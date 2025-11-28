# academico/utils/excel.py

import csv
import io
from typing import Iterable, Tuple

from django.core.files.base import ContentFile

from academico.models import Calificacion, Evaluacion
from usuarios.models import User


# ============================================================
#  EXPORTAR NOTAS A CSV (EXCEL)
# ============================================================

def generar_csv_notas_evaluacion(evaluacion: Evaluacion) -> str:
    """
    Genera un CSV (separado por ;) con las notas de una evaluación.

    Columnas:
      - ID estudiante
      - RUT
      - Nombre
      - Curso
      - Asignatura
      - Nota
      - Observaciones
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';')

    writer.writerow([
        "ID estudiante",
        "RUT",
        "Nombre",
        "Curso",
        "Asignatura",
        "Nota",
        "Observaciones",
    ])

    calificaciones = (
        Calificacion.objects
        .select_related("estudiante", "evaluacion__curso", "evaluacion__asignatura")
        .filter(evaluacion=evaluacion)
        .order_by("estudiante__last_name", "estudiante__first_name")
    )

    for c in calificaciones:
        estudiante: User = c.estudiante
        curso = c.evaluacion.curso
        asignatura = c.evaluacion.asignatura
        writer.writerow([
            estudiante.id,
            estudiante.rut or "",
            f"{estudiante.first_name} {estudiante.last_name}",
            str(curso) if curso else "",
            str(asignatura) if asignatura else "",
            f"{c.nota:.2f}",
            c.observaciones or "",
        ])

    content = buffer.getvalue()
    buffer.close()
    return content


def adjuntar_csv_notas_a_evaluacion(evaluacion: Evaluacion, field_name: str = "archivo_notas") -> None:
    """
    Genera un CSV de notas y lo guarda en un FileField de la evaluación (si existe).
    Útil si más adelante agregas un campo tipo FileField a Evaluacion.
    """
    csv_content = generar_csv_notas_evaluacion(evaluacion)
    file_name = f"notas_evaluacion_{evaluacion.id}.csv"

    archivo_field = getattr(evaluacion, field_name, None)
    if archivo_field is None:
        return

    archivo_field.save(
        file_name,
        ContentFile(csv_content.encode("utf-8")),
        save=False,
    )
    evaluacion.save(update_fields=[field_name])


# ============================================================
#  IMPORTAR NOTAS DESDE CSV (EXCEL)
# ============================================================

def parsear_csv_notas(file) -> Iterable[Tuple[int, float, str]]:
    """
    Parsea un archivo CSV (InMemoryUploadedFile, TemporaryUploadedFile, etc.)
    y retorna un iterable de tuplas:

      (id_estudiante, nota, observaciones)

    Se espera encabezado con al menos:
      - "ID estudiante"
      - "Nota"
      (Observaciones es opcional)

    Si usas delimitador diferente, ajusta el `delimiter`.
    """
    # Aceptamos bytes o string
    if hasattr(file, "read"):
        raw = file.read().decode("utf-8")
    else:
        raw = str(file)

    buffer = io.StringIO(raw)
    reader = csv.DictReader(buffer, delimiter=';')

    for row in reader:
        # Ignoramos filas sin ID o sin nota
        if not row.get("ID estudiante") or not row.get("Nota"):
            continue

        try:
            estudiante_id = int(row["ID estudiante"])
        except ValueError:
            continue

        try:
            nota = float(str(row["Nota"]).replace(",", "."))
        except ValueError:
            continue

        observaciones = row.get("Observaciones", "").strip()

        yield estudiante_id, nota, observaciones


def importar_notas_desde_csv_para_evaluacion(
    evaluacion: Evaluacion,
    file,
    actualizar_existentes: bool = True,
) -> int:
    """
    Importa notas desde un CSV para una evaluación específica.

    - Busca cada estudiante por ID.
    - Crea o actualiza la Calificacion correspondiente.

    Retorna la cantidad de registros de nota procesados correctamente.
    """
    registros = parsear_csv_notas(file)
    procesados = 0

    for estudiante_id, nota, observaciones in registros:
        try:
            estudiante = User.objects.get(id=estudiante_id)
        except User.DoesNotExist:
            continue

        if actualizar_existentes:
            obj, _created = Calificacion.objects.update_or_create(
                evaluacion=evaluacion,
                estudiante=estudiante,
                defaults={
                    "nota": nota,
                    "observaciones": observaciones,
                },
            )
        else:
            # Solo crear si no existe
            obj, created = Calificacion.objects.get_or_create(
                evaluacion=evaluacion,
                estudiante=estudiante,
                defaults={
                    "nota": nota,
                    "observaciones": observaciones,
                },
            )
            if not created:
                # Si ya existía y no queremos actualizar, lo saltamos
                continue

        procesados += 1

    return procesados
