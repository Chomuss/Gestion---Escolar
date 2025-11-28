from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


# Vista que expone el schema OpenAPI (JSON)
schema_view = SpectacularAPIView.as_view()


# UI Swagger
swagger_ui_view = SpectacularSwaggerView.as_view(
    url_name="api-schema",
)


# UI Redoc
redoc_ui_view = SpectacularRedocView.as_view(
    url_name="api-schema",
)
