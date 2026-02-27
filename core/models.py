from django.db import models

# Create your models here.
class Business_Config(models.Model):
    business_name = models.CharField(max_length=100)
    time_zone = models.CharField(max_length=100)
    locale = models.CharField(max_length=100)
    distance_unit = models.CharField(max_length=100)
    max_valid_distance = models.IntegerField()
    min_time_between_visits = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)
    logo_url = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        if not self.pk and Business_Config.objects.exists():
            return
        return super(Business_Config, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    def __str__(self):
        return f"{self.business_name}"