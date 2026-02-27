from django.urls import path
from .views import *

urlpatterns = [
    path('business-config/', BusinessConfigView, name='business-config'),
]