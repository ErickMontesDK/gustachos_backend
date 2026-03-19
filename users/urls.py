from django.urls import path
from .views import *

urlpatterns = [
    path('users/', user_list, name='user_list'),
    path('users/<int:pk>/', user_detail, name='user_detail'),
    path('users/me/', user_me, name='user_me'),
    path('users/me/dashboard/', user_dashboard, name='user_dashboard'),
    path('users/me/change-password/', update_user_password, name='update_user_password'),
    path('users/<int:pk>/change-password/', update_user_password, name='update_user_password'),
    path('users/<int:pk>/restore/', user_restore, name='user_restore'),
    path('users/dashboard/stats/', dashboard_stats, name='dashboard_stats'),
]