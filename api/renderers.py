from collections.abc import Mapping
from rest_framework.renderers import JSONRenderer


class CustomJSONRenderer(JSONRenderer):
    """
    Renderer global de la API.

    - Envuelve respuestas exitosas en un formato estándar.
    - Deja las respuestas de error tal como las deja el exception handler.
    """

    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        response = renderer_context.get("response")

        if response is None:
            return super().render(data, accepted_media_type, renderer_context)

        if response.exception:
            return super().render(data, accepted_media_type, renderer_context)

        # Caso paginado estándar DRF
        if isinstance(data, Mapping) and "results" in data and "count" in data:
            formatted = {
                "success": True,
                "count": data.get("count"),
                "next": data.get("next"),
                "previous": data.get("previous"),
                "results": data.get("results"),
            }
            return super().render(formatted, accepted_media_type, renderer_context)

        formatted = {
            "success": True,
            "data": data,
        }
        return super().render(formatted, accepted_media_type, renderer_context)
