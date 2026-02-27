from django.urls import path
from .views import *

urlpatterns = [
    path('users/', user_list, name='user_list'),
    path('users/<int:pk>/', user_detail, name='user_detail'),
    path('users/me/', user_me, name='user_me'),
    path('users/password/', update_user_password, name='update_user_password'),
]