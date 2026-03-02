from django.db import models

# Create your models here.
class Business_Config(models.Model):
    UNITS = (
        ('m', 'Meters'),
        ('ft', 'Feet'),
    )
    
    business_name = models.CharField(max_length=100)
    time_zone = models.CharField(max_length=100)
    locale = models.CharField(max_length=100)
    distance_unit = models.CharField(max_length=100, choices=UNITS, default='m')
    max_valid_distance = models.IntegerField(default=100, help_text="Maximum valid distance in meters")
    min_time_between_visits = models.IntegerField(default=10, help_text="Minimum time between visits in minutes")
    updated_at = models.DateTimeField(auto_now=True)
    logo_url = models.CharField(max_length=100, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk and Business_Config.objects.exists():
            return
        return super(Business_Config, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    def __str__(self):
        return f"{self.business_name}"