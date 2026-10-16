from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Safe representation of a User for public and authenticated responses.
    Excludes sensitive fields (passwords, groups, user_permissions).
    """
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'is_active',
            'date_joined',
        ]
        read_only_fields = [
            'id',
            'username',
            'role',
            'is_active',
            'date_joined',
        ]


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for public customer registration.
    Enforces CUSTOMER role and prevents role escalation.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Account password conforming to security rules.'
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'},
        help_text='Confirmation of the account password.'
    )
    password_confirmation = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'},
        help_text='Alternative alias for password confirmation.'
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',
            'password_confirm',
            'password_confirmation',
            'first_name',
            'last_name',
            'role',
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'email': {'required': True},
            'role': {'required': False},
        }

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value.strip()).exists():
            raise serializers.ValidationError('A user with that username already exists.')
        return value.strip()

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError('Email field is required.')
        normalized_email = value.strip().lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError('A user with that email already exists.')
        return normalized_email

    def validate(self, attrs):
        # Support both password_confirm and password_confirmation
        confirm = attrs.get('password_confirm') or attrs.get('password_confirmation')
        password = attrs.get('password')

        if confirm and password != confirm:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })

        # Check client-supplied role attempts
        requested_role = attrs.get('role')
        if requested_role and requested_role != User.Role.CUSTOMER:
            raise serializers.ValidationError({
                'role': 'Public registration is only permitted for CUSTOMER accounts. Privileged roles cannot be self-assigned.'
            })

        # Validate password using Django's configured password validators
        user_candidate = User(
            username=attrs.get('username', ''),
            email=attrs.get('email', '')
        )
        try:
            password_validation.validate_password(password, user=user_candidate)
        except DjangoValidationError as err:
            raise serializers.ValidationError({'password': list(err.messages)})

        return attrs

    def create(self, validated_data):
        # Remove confirmation fields and any client-provided role
        validated_data.pop('password_confirm', None)
        validated_data.pop('password_confirmation', None)
        validated_data.pop('role', None)

        # Force CUSTOMER role for public registration
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=User.Role.CUSTOMER,
            is_staff=False,
            is_superuser=False,
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    JWT login serializer providing access and refresh tokens along with safe user info.
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating authenticated user profile.
    Only allows first_name, last_name, and email to be updated.
    Strictly forbids role, is_staff, is_superuser, username, or id changes.
    """
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'date_joined',
        ]
        read_only_fields = [
            'id',
            'username',
            'role',
            'date_joined',
        ]

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError('Email field cannot be empty.')
        normalized_email = value.strip().lower()
        current_user = self.instance
        if User.objects.filter(email__iexact=normalized_email).exclude(pk=current_user.pk).exists():
            raise serializers.ValidationError('A user with that email already exists.')
        return normalized_email

    def validate(self, attrs):
        # Check if caller tried to submit prohibited fields in the payload
        initial_data = getattr(self, 'initial_data', {})
        prohibited_fields = {'role', 'is_staff', 'is_superuser', 'username', 'id', 'password'}
        attempted_prohibited = prohibited_fields.intersection(initial_data.keys())
        if attempted_prohibited:
            # If the value differs from current, explicitly reject
            for field in attempted_prohibited:
                if field == 'role' and str(initial_data['role']) != str(self.instance.role):
                    raise serializers.ValidationError({
                        'role': 'You are not permitted to change your role.'
                    })
                if field in ('is_staff', 'is_superuser') and bool(initial_data[field]) != bool(getattr(self.instance, field)):
                    raise serializers.ValidationError({
                        field: f'You are not permitted to modify {field}.'
                    })
                if field in ('username', 'id', 'password'):
                    raise serializers.ValidationError({
                        field: f'Modifying {field} is not permitted via this endpoint.'
                    })

        return attrs
