from rest_framework import serializers
from .models import Business_Config

class Business_ConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business_Config
        fields = '__all__'