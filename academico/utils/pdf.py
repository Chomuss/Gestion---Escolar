from io import BytesIO
from typing import Iterable, List

from django.core.files.base import ContentFile

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from academico.models import ReporteNotasPeriodo


def generar_pdf_simple(
    titulo: str,
    lineas: Iterable[str],
    pagesize=A4,
) -> bytes:
    """
    Genera un PDF sencillo con un título y una lista de líneas de texto.

    Retorna el contenido del PDF en bytes.
    """
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=pagesize)

    width, height = pagesize

    # Título
    y = height - 50
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, y, titulo)

    # Contenido
    y -= 40
    p.setFont("Helvetica", 11)

    for linea in lineas:
        if y < 50: 
            p.showPage()
            y = height - 50
            p.setFont("Helvetica", 11)

        p.drawString(40, y, linea)
        y -= 18

    p.showPage()
    p.save()

    pdf_value = buffer.getvalue()
    buffer.close()
    return pdf_value


def generar_pdf_reporte_notas(reporte: ReporteNotasPeriodo) -> bytes:
    """
    Genera un PDF muy simple para un ReporteNotasPeriodo, con
    información básica (curso, asignatura, periodo, etc.).

    La idea es que luego puedas mejorarlo con más diseño si quieres.
    """
    curso = reporte.curso
    asignatura = reporte.asignatura
    periodo = reporte.periodo

    titulo = "Reporte de notas por período"

    lineas: List[str] = [
        f"Curso: {curso}",
        f"Asignatura: {asignatura}",
        f"Periodo: {periodo}",
        "",
        "Este es un reporte resumen de notas. Para detalle completo,",
        "puede descargar el archivo Excel asociado.",
    ]

    return generar_pdf_simple(titulo, lineas)


def adjuntar_pdf_a_reporte(reporte: ReporteNotasPeriodo) -> None:
    """
    Genera un PDF simple para el ReporteNotasPeriodo y lo guarda
    en el campo archivo_pdf.
    """
    pdf_bytes = generar_pdf_reporte_notas(reporte)

    file_name = (
        f"reporte_notas_curso{reporte.curso.id}_"
        f"asig{reporte.asignatura.id}_"
        f"periodo{reporte.periodo.id}.pdf"
    )

    reporte.archivo_pdf.save(
        file_name,
        ContentFile(pdf_bytes),
        save=False,
    )
    reporte.save(update_fields=["archivo_pdf"])
