from rest_framework import serializers
from .models import Business_Config
import zoneinfo

class Business_ConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business_Config
        fields = '__all__'

    def validate(self, attrs):
        if attrs['max_valid_distance'] < 0:
            raise serializers.ValidationError("Max valid distance must be positive")
        if attrs['min_time_between_visits'] < 0:
            raise serializers.ValidationError("Min time between visits must be positive")
        if attrs['time_zone'] not in zoneinfo.available_timezones():
            raise serializers.ValidationError("Invalid time zone")
        return attrs

class PublicBusiness_ConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business_Config
        fields = ['business_name', 'logo_url']
        read_only_fields = ['business_name', 'logo_url']