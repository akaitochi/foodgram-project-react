from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    """Кастомный паджинатор с параметром limit."""

    page_size_query_param = 'limit'
    page_size = 6
