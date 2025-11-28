from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Paginación estándar para toda la API.

    - page_size: cantidad por defecto
    - page_size_query_param: permite al cliente cambiar el tamaño
    - max_page_size: límite para que no pidan 100000 registros de golpe
    """
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"
