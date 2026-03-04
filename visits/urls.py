from django.urls import path
from .views import *

urlpatterns = [
    path('client-types/', get_client_types, name='client_types'),
    path('client-types/<int:pk>/', client_type_detail, name='client_type_detail'),

    path('visits/', visit_list, name='visit_list'),
    path('visits/<int:pk>/', visit_detail, name='visit_detail'),
    path('visits/export/', visit_list_export, name='visit_list_export'),
    path('visits/restore/<int:pk>/', visits_restore, name='visits_restore'),

    path('clients/', client_list, name='client_list'),
    path('clients/export/', client_list_export, name='client_list_export'),
    path('clients/code-available/', client_code_available, name='client_code_available'),
    path('clients/code/<str:code>/', client_by_code, name='client_by_code'),
    path('clients/<int:id>/', client_detail, name='client_detail'),
    path('clients/map/', client_list_for_map, name='client_list_for_map'),
    path('clients/restore/<int:pk>/', client_restore, name='client_restore'),
]