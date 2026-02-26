from django.urls import path
from .views import *

urlpatterns = [
    path('users/', user_list, name='user_list'),
    path('users/<int:pk>/', user_detail, name='user_detail'),
]