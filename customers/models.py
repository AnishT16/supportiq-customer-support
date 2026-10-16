from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

phone_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)


class Customer(models.Model):
    """
    SupportIQ Customer Profile.
    Represents customer identity, contact information, and delivery/support details.
    Each customer is linked one-to-one with a User account.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile',
        help_text='Associated SupportIQ user account.'
    )
    name = models.CharField(
        max_length=255,
        help_text='Full name of the customer.'
    )
    email = models.EmailField(
        unique=True,
        help_text='Unique contact email address for the customer.'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[phone_validator],
        help_text='Contact phone number with optional country code.'
    )
    address = models.TextField(
        blank=True,
        help_text='Primary billing / delivery address.'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Timestamp when the customer profile was created.'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Timestamp when the customer profile was last updated.'
    )

    class Meta:
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Normalize email to lowercase
        if self.email:
            self.email = self.email.strip().lower()
        # Default name or email from user if not explicitly provided
        if self.user:
            if not self.email and self.user.email:
                self.email = self.user.email.strip().lower()
            if not self.name:
                self.name = self.user.get_full_name() or self.user.username
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.email})"
