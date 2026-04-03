from django.urls import path

from .views import search_facets_view, search_query_view, search_status_view

urlpatterns = [
    path("", search_status_view, name="search-status"),
    path("query/", search_query_view, name="search-query"),
    path("facets/", search_facets_view, name="search-facets"),
]
