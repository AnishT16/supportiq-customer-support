from django.contrib.auth import get_user_model
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from accounts.models import User
from customers.models import Customer
from .models import Ticket

UserModel = get_user_model()


class TicketSerializer(serializers.ModelSerializer):
    """
    Serializer for Ticket management.
    Enforces role-based field protections:
    - Customers cannot self-assign, reassign, change status, or pick arbitrary customers.
    - Agents cannot reassign tickets to others.
    - Managers/Admins can manage assignments and status.
    """
    customer_id = serializers.IntegerField(
        required=False,
        write_only=True,
        help_text='ID of the customer for whom the ticket is created (Staff only).'
    )
    customer_name = serializers.CharField(
        source='customer.name',
        read_only=True,
        help_text='Name of the customer.'
    )
    customer_email = serializers.CharField(
        source='customer.email',
        read_only=True,
        help_text='Email address of the customer.'
    )
    assigned_to_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        write_only=True,
        help_text='ID of the support agent or staff user assigned (Manager/Admin only).'
    )
    assigned_to_name = serializers.SerializerMethodField(
        read_only=True,
        help_text='Full name or username of assigned support agent.'
    )
    assigned_to_username = serializers.CharField(
        source='assigned_to.username',
        read_only=True,
        default=None,
        help_text='Username of assigned agent.'
    )

    class Meta:
        model = Ticket
        fields = [
            'id',
            'ticket_number',
            'customer_id',
            'customer_name',
            'customer_email',
            'subject',
            'description',
            'category',
            'priority',
            'status',
            'assigned_to_id',
            'assigned_to_name',
            'assigned_to_username',
            'created_at',
            'updated_at',
            'resolved_at',
        ]
        read_only_fields = [
            'id',
            'ticket_number',
            'customer_name',
            'customer_email',
            'assigned_to_name',
            'assigned_to_username',
            'created_at',
            'updated_at',
            'resolved_at',
        ]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.get_full_name() or obj.assigned_to.username
        return None

    def validate_category(self, value):
        if value not in Ticket.Category.values:
            raise serializers.ValidationError(f"Invalid category '{value}'. Allowed: {Ticket.Category.values}")
        return value

    def validate_priority(self, value):
        if value not in Ticket.Priority.values:
            raise serializers.ValidationError(f"Invalid priority '{value}'. Allowed: {Ticket.Priority.values}")
        return value

    def validate_status(self, value):
        if value not in Ticket.Status.values:
            raise serializers.ValidationError(f"Invalid status '{value}'. Allowed: {Ticket.Status.values}")
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user if request else None

        # Handle Ticket Creation
        if not self.instance:
            if user.role == User.Role.CUSTOMER:
                # Customers automatically own tickets they create
                if not hasattr(user, 'customer_profile'):
                    raise serializers.ValidationError({
                        'detail': 'You must create a customer profile before opening a support ticket.'
                    })
                attrs['resolved_customer'] = user.customer_profile
                # Enforce default initial status for customers
                attrs['status'] = Ticket.Status.OPEN
                # Customers cannot assign tickets
                attrs.pop('assigned_to_id', None)
            else:
                # Staff creating ticket on behalf of a customer
                supplied_customer_id = attrs.get('customer_id')
                if not supplied_customer_id:
                    raise serializers.ValidationError({
                        'customer_id': 'customer_id is required when creating a ticket as staff.'
                    })
                try:
                    target_customer = Customer.objects.get(pk=supplied_customer_id)
                except Customer.DoesNotExist:
                    raise serializers.ValidationError({
                        'customer_id': f'Customer with ID {supplied_customer_id} does not exist.'
                    })
                attrs['resolved_customer'] = target_customer

            # Validate assigned_to_id if provided by Manager/Admin
            assigned_id = attrs.get('assigned_to_id')
            if assigned_id is not None:
                if user.role not in [User.Role.ADMIN, User.Role.MANAGER]:
                    raise serializers.ValidationError({
                        'assigned_to_id': 'Only Managers and Admins can assign tickets upon creation.'
                    })
                try:
                    assigned_user = UserModel.objects.get(pk=assigned_id)
                except UserModel.DoesNotExist:
                    raise serializers.ValidationError({
                        'assigned_to_id': f'User with ID {assigned_id} does not exist.'
                    })
                if assigned_user.role == User.Role.CUSTOMER:
                    raise serializers.ValidationError({
                        'assigned_to_id': 'Tickets cannot be assigned to customer accounts.'
                    })
                attrs['resolved_assigned_to'] = assigned_user

            return attrs

        # Handle Ticket Update
        if self.instance:
            # Prevent altering ticket ownership
            if 'customer_id' in attrs:
                if attrs['customer_id'] != self.instance.customer_id:
                    raise serializers.ValidationError({
                        'customer_id': 'Reassigning a ticket to a different customer is not permitted.'
                    })

            # Customer update constraints
            if user.role == User.Role.CUSTOMER:
                prohibited_fields = {'status', 'priority', 'assigned_to_id'}
                attempted = prohibited_fields.intersection(self.initial_data.keys())
                if attempted:
                    for field in attempted:
                        if field == 'status' and attrs.get('status') != self.instance.status:
                            raise serializers.ValidationError({
                                'status': 'Customers cannot directly alter ticket status. Use resolution/close actions.'
                            })
                        if field == 'priority' and attrs.get('priority') != self.instance.priority:
                            raise serializers.ValidationError({
                                'priority': 'Customers cannot change priority once a ticket is submitted.'
                            })
                        if field == 'assigned_to_id':
                            raise serializers.ValidationError({
                                'assigned_to_id': 'Customers cannot assign or reassign tickets.'
                            })

            # Agent update constraints
            if user.role == User.Role.AGENT:
                if 'assigned_to_id' in self.initial_data:
                    if attrs.get('assigned_to_id') != self.instance.assigned_to_id:
                        raise serializers.ValidationError({
                            'assigned_to_id': 'Agents cannot reassign tickets. Manager or Admin privileges required.'
                        })

            # Validate assigned_to_id if submitted by Manager/Admin
            if 'assigned_to_id' in attrs:
                assigned_id = attrs['assigned_to_id']
                if assigned_id is None:
                    attrs['resolved_assigned_to'] = None
                else:
                    try:
                        assigned_user = UserModel.objects.get(pk=assigned_id)
                    except UserModel.DoesNotExist:
                        raise serializers.ValidationError({
                            'assigned_to_id': f'User with ID {assigned_id} does not exist.'
                        })
                    if assigned_user.role == User.Role.CUSTOMER:
                        raise serializers.ValidationError({
                            'assigned_to_id': 'Tickets cannot be assigned to customer accounts.'
                        })
                    attrs['resolved_assigned_to'] = assigned_user

        return attrs

    def create(self, validated_data):
        customer = validated_data.pop('resolved_customer')
        assigned_to = validated_data.pop('resolved_assigned_to', None)
        validated_data.pop('customer_id', None)
        validated_data.pop('assigned_to_id', None)
        return Ticket.objects.create(
            customer=customer,
            assigned_to=assigned_to,
            **validated_data
        )

    def update(self, instance, validated_data):
        validated_data.pop('customer_id', None)
        validated_data.pop('resolved_customer', None)
        if 'resolved_assigned_to' in validated_data:
            instance.assigned_to = validated_data.pop('resolved_assigned_to')
        validated_data.pop('assigned_to_id', None)
        return super().update(instance, validated_data)


class TicketAssignSerializer(serializers.Serializer):
    """
    Serializer for explicitly assigning a ticket to an eligible agent or clearing assignment.
    """
    assigned_to_id = serializers.IntegerField(
        required=True,
        allow_null=True,
        help_text='ID of the agent user to assign, or null to unassign.'
    )

    def validate_assigned_to_id(self, value):
        if value is None:
            return None
        try:
            target_user = UserModel.objects.get(pk=value)
        except UserModel.DoesNotExist:
            raise serializers.ValidationError(f"User with ID {value} does not exist.")
        if target_user.role == User.Role.CUSTOMER:
            raise serializers.ValidationError("Tickets cannot be assigned to customer users.")
        return target_user


class TicketStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for explicit workflow status transitions.
    """
    status = serializers.ChoiceField(
        choices=Ticket.Status.choices,
        required=True,
        help_text='Target status to transition the ticket to.'
    )
