from django.db import migrations
import os

def create_superuser(apps, schema_editor):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username=os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin'),
            email=os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@admin.com'),
            password=os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'password123')
        )

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_is_deleted'),
    ]

    operations = [
        migrations.RunPython(create_superuser),
    ]