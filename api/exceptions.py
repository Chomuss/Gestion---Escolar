from typing import Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.exceptions import ValidationError


def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    """
    Manejador global de errores para la API.

    - Se apoya en el handler por defecto de DRF.
    - Envuelve la respuesta en un formato estándar:
      {
        "success": false,
        "message": "Mensaje principal",
        "errors": {...},
        "status_code": 400
      }
    """

    response = drf_exception_handler(exc, context)

    if response is None:
        return response

    # Data original que puso DRF
    original_data: Any = response.data

    # Mensaje principal
    message = None
    errors = None

    if isinstance(original_data, dict):
        if "detail" in original_data:
            message = original_data["detail"]
            errors = {k: v for k, v in original_data.items() if k != "detail"}
            if not errors:
                errors = None
        else:
            message = "Se produjo un error al procesar la solicitud."
            errors = original_data

    elif isinstance(original_data, list):
        message = "; ".join([str(item) for item in original_data])
        errors = {"non_field_errors": original_data}
    else:
        message = str(original_data)
        errors = None

    if isinstance(exc, ValidationError) and response.status_code == status.HTTP_400_BAD_REQUEST:
        if message is None:
            message = "Los datos enviados no son válidos."

    formatted = {
        "success": False,
        "message": message,
        "errors": errors,
        "status_code": response.status_code,
    }

    response.data = formatted
    return response
