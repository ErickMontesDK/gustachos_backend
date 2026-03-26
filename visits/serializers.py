from rest_framework import serializers
from .models import Client, Visit, ClientType, Route
from users.models import User
from math import radians, sin, asin, sqrt, cos
from datetime import timedelta
from core.models import Business_Config


class ClientTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientType
        fields = '__all__'

class ClientSerializer(serializers.ModelSerializer):
    client_type_name = serializers.CharField(source='client_type.name', read_only=True)
    full_address = serializers.CharField(source='get_full_address', read_only=True)
    client_type = serializers.PrimaryKeyRelatedField(
        queryset=ClientType.objects.all(), 
        allow_null=True, 
        required=False
    )
    status = serializers.CharField(read_only=True)
    last_sale_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Client
        fields = [
            'id', 
            'code', 
            'name', 
            "client_type", 
            "client_type_name",
            'address', 
            'neighborhood', 
            'municipality', 
            'state', 
            'full_address', 
            'latitude', 
            'longitude', 
            'sector', 
            'market',
            'is_active',
            'status',
            'last_sale_date',
            'is_deleted'
        ]

    def to_internal_value(self, data):
        data = data.copy()
        if 'client_type' in data:
            val = data.get('client_type')
            if val == "" or val == "0" or val == 0 or val == "None":
                data['client_type'] = None
        return super().to_internal_value(data)

class ClientForMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            'id', 
            'name', 
            'latitude', 
            'longitude', 
            'client_type'
        ]

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['full_name', 'role', 'is_deleted']

class VisitSerializer(serializers.ModelSerializer):
    client_details = ClientSerializer(source='client', read_only=True)
    deliverer_details = UserSerializer(source='deliverer', read_only=True)


    class Meta:
        model = Visit
        fields = [
            'id', 
            'client',
            'deliverer',
            'client_details', 
            'deliverer_details', 
            'visited_at', 
            'latitude_recorded', 
            'longitude_recorded',
            'is_productive', 
            'is_valid', 
            'notes',
            'is_deleted'
        ]

    def validate(self, data):
        business_config = Business_Config.objects.first()
        max_distance = business_config.max_valid_distance
        distance_unit = business_config.distance_unit
        time_limit = business_config.min_time_between_visits

        client = data.get('client')
        lat_scan = data.get('latitude_recorded')
        lng_scan = data.get('longitude_recorded')


        if client and lat_scan and lng_scan:
            client_lat = client.latitude
            client_lng = client.longitude
            earth_radius = 6371008.8
            lat1, lon1 = map(radians, [float(client_lat), float(client_lng)])
            lat2, lon2 = map(radians, [float(lat_scan), float(lng_scan)])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
            c = 2 * asin(sqrt(a))
            distance = earth_radius * c

            data['distance_from_client'] = distance
            if distance_unit == 'ft':
                max_distance_meters = max_distance / 3.28084  
            else:
                max_distance_meters = max_distance  

            data['is_valid'] = distance < max_distance_meters

        deliverer = data.get('deliverer')
        visited_at = data.get('visited_at')

        if deliverer and visited_at:
            suspicius_time = time_limit
            start_range = visited_at - timedelta(minutes=suspicius_time)
            end_range = visited_at + timedelta(minutes=suspicius_time)
            
            duplicate_visits = Visit.objects.filter(
                deliverer=deliverer,
                is_deleted=False,
                visited_at__range=(start_range, end_range),
                is_valid=True
            )
            
            if self.instance and self.instance.pk:
                duplicate_visits = duplicate_visits.exclude(pk=self.instance.pk)
                
            if duplicate_visits.exists():
                data['is_valid'] = False
            
        return data


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ['id', 'name', 'deliverer', 'day_of_week']
