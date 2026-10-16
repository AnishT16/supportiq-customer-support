import secrets
from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_unique_ticket_number():
    """
    Generates a secure, human-readable, collision-resistant ticket reference.
    Format: TIK-YYYYMMDD-XXXXXX
    """
    date_str = timezone.now().strftime('%Y%m%d')
    random_suffix = secrets.token_hex(3).upper()
    return f"TIK-{date_str}-{random_suffix}"


class Ticket(models.Model):
    """
    SupportIQ Customer Support Ticket.
    Tracks issues raised by customers, agent assignments, priority, and resolution lifecycle.
    """
    class Category(models.TextChoices):
        DELIVERY = 'DELIVERY', 'Delivery & Shipping'
        PAYMENT = 'PAYMENT', 'Payment & Billing'
        REFUND = 'REFUND', 'Refund Request'
        CANCELLATION = 'CANCELLATION', 'Order Cancellation'
        ACCOUNT = 'ACCOUNT', 'Account & Security'
        PRODUCT = 'PRODUCT', 'Product Issue'
        OTHER = 'OTHER', 'Other / General'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        WAITING_FOR_CUSTOMER = 'WAITING_FOR_CUSTOMER', 'Waiting for Customer'
        RESOLVED = 'RESOLVED', 'Resolved'
        CLOSED = 'CLOSED', 'Closed'

    ticket_number = models.CharField(
        max_length=32,
        unique=True,
        editable=False,
        db_index=True,
        help_text='Unique identifier for the ticket (e.g. TIK-20261016-A1B2C3).'
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='tickets',
        help_text='Customer who owns this ticket.'
    )
    subject = models.CharField(
        max_length=255,
        db_index=True,
        help_text='Concise summary of the support inquiry or problem.'
    )
    description = models.TextField(
        help_text='Detailed explanation of the issue submitted by the customer.'
    )
    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.OTHER,
        db_index=True,
        help_text='Category of the support request.'
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True,
        help_text='Urgency/severity level of the issue.'
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
        help_text='Current progress status of the ticket.'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_tickets',
        help_text='Support agent or manager currently assigned to handle this ticket.'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text='Timestamp when the ticket was created.'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Timestamp when the ticket was last updated.'
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when the ticket was marked as resolved or closed.'
    )

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['status', 'priority']),
        ]

    def clean(self):
        super().clean()
        # Ensure assigned_to is a privileged user (AGENT, MANAGER, ADMIN), not a customer
        if self.assigned_to and hasattr(self.assigned_to, 'role'):
            from accounts.models import User
            if self.assigned_to.role == User.Role.CUSTOMER:
                from django.core.exceptions import ValidationError
                raise ValidationError({'assigned_to': 'Tickets cannot be assigned to customer users.'})

    def save(self, *args, **kwargs):
        # Auto-generate unique ticket_number if not set
        if not self.ticket_number:
            while True:
                candidate = generate_unique_ticket_number()
                if not Ticket.objects.filter(ticket_number=candidate).exists():
                    self.ticket_number = candidate
                    break

        # Maintain resolved_at timestamp consistently
        if self.status in [self.Status.RESOLVED, self.Status.CLOSED]:
            if not self.resolved_at:
                self.resolved_at = timezone.now()
        else:
            # Reopening or in-progress clears resolved_at
            if self.resolved_at:
                self.resolved_at = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.ticket_number}] {self.subject} ({self.get_status_display()})"
