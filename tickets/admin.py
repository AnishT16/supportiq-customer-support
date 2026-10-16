from django.contrib import admin
from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'ticket_number',
        'subject',
        'customer',
        'category',
        'priority',
        'status',
        'assigned_to',
        'created_at',
        'resolved_at',
    )
    list_filter = ('status', 'priority', 'category', 'created_at', 'resolved_at')
    search_fields = ('ticket_number', 'subject', 'description', 'customer__name', 'customer__email')
    readonly_fields = ('ticket_number', 'created_at', 'updated_at', 'resolved_at')
    ordering = ('-created_at',)
