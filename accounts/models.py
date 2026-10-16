from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    SupportIQ Custom User Model with role-based access control.
    Roles:
      - CUSTOMER: Standard end-user seeking support or viewing orders/tickets.
      - AGENT: Support representative managing tickets and handling conversations.
      - MANAGER: Support supervisor viewing analytics, predictions, and high-risk cases.
      - ADMIN: Platform administrator with full access to policies and configurations.
    """
    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Customer'
        AGENT = 'AGENT', 'Agent'
        MANAGER = 'MANAGER', 'Manager'
        ADMIN = 'ADMIN', 'Admin'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        help_text='Designates the role and authorization tier of the user.',
    )
    email = models.EmailField(
        unique=True,
        blank=False,
        error_messages={
            'unique': 'A user with that email already exists.',
        },
    )

    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER

    @property
    def is_agent(self):
        return self.role == self.Role.AGENT

    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    def __str__(self):
        return f"{self.username} ({self.role})"
