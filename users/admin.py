from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register your models here.
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("id", "full_name", "username", "email", "role", "is_deleted")
    list_filter = ("role", "is_deleted")
    search_fields = ('username', 'email')
    ordering = ('username',)

    fieldsets = UserAdmin.fieldsets + (
        (None, {"fields": ("role", "is_deleted")}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {
            "classes": ("wide",),
            "fields": ("role", "email", "first_name", "last_name", "is_deleted", "password",),
        }),
    )

admin.site.register(User, CustomUserAdmin)