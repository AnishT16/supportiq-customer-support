from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Customer

User = get_user_model()


class CustomerSerializer(serializers.ModelSerializer):
    """
    Serializer for Customer identity and profile information.
    Ensures safe representation without exposing any sensitive auth details.
    """
    user_id = serializers.IntegerField(
        required=False,
        write_only=True,
        help_text='User ID to link to this customer (Admin/Manager only).'
    )
    username = serializers.CharField(
        source='user.username',
        read_only=True,
        help_text='Username of the linked User account.'
    )
    user_role = serializers.CharField(
        source='user.role',
        read_only=True,
        help_text='Role of the linked User account.'
    )

    class Meta:
        model = Customer
        fields = [
            'id',
            'user_id',
            'username',
            'user_role',
            'name',
            'email',
            'phone',
            'address',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'username',
            'user_role',
            'created_at',
            'updated_at',
        ]

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError('Email address cannot be empty.')
        normalized = value.strip().lower()
        existing = Customer.objects.filter(email__iexact=normalized)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError('A customer with that email already exists.')
        return normalized

    def validate(self, attrs):
        request = self.context.get('request')
        current_user = request.user if request else None

        # On update: protect ownership field from modification
        if self.instance:
            if 'user_id' in attrs:
                if attrs['user_id'] != self.instance.user_id:
                    raise serializers.ValidationError({
                        'user_id': 'Reassigning customer profile ownership to another user is not permitted.'
                    })
            return attrs

        # On create: determine and validate linked User
        if not self.instance:
            target_user = None
            if current_user and current_user.role == User.Role.CUSTOMER:
                # Customers can only create a profile for themselves
                if hasattr(current_user, 'customer_profile'):
                    raise serializers.ValidationError({
                        'detail': 'A customer profile already exists for your account.'
                    })
                target_user = current_user
            else:
                # Staff/Admin/Manager creating customer
                supplied_user_id = attrs.get('user_id')
                if supplied_user_id:
                    try:
                        target_user = User.objects.get(pk=supplied_user_id)
                    except User.DoesNotExist:
                        raise serializers.ValidationError({
                            'user_id': f'User with ID {supplied_user_id} does not exist.'
                        })
                    if hasattr(target_user, 'customer_profile'):
                        raise serializers.ValidationError({
                            'user_id': 'A customer profile already exists for this user.'
                        })
                else:
                    # If staff didn't supply user_id, check if current staff user has no profile
                    if hasattr(current_user, 'customer_profile'):
                        raise serializers.ValidationError({
                            'user_id': 'user_id is required when creating a customer profile as staff/agent.'
                        })
                    target_user = current_user

            attrs['resolved_user'] = target_user

        return attrs

    def create(self, validated_data):
        target_user = validated_data.pop('resolved_user')
        validated_data.pop('user_id', None)
        return Customer.objects.create(user=target_user, **validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('user_id', None)
        validated_data.pop('resolved_user', None)
        return super().update(instance, validated_data)
