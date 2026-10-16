from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'user', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'email', 'phone', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
