from django.contrib import admin
from .models import Business_Config

# Register your models here.
class Business_ConfigAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'time_zone', 'locale', 'distance_unit', 'max_valid_distance', 'min_time_between_visits', 'updated_at', 'logo_url')

admin.site.register(Business_Config, Business_ConfigAdmin)