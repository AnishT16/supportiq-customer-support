from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileUpdateSerializer,
)

User = get_user_model()


@extend_schema(
    summary="Register a new customer account",
    description="Registers a new customer. The account is assigned the CUSTOMER role by default. Privileged role assignment is prohibited.",
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(response=UserSerializer, description="Customer registered successfully."),
        400: OpenApiResponse(description="Validation error (e.g., duplicate username/email, mismatched passwords, weak password)."),
    },
    tags=["Authentication"],
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        output_serializer = UserSerializer(user, context=self.get_serializer_context())
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Authenticate and obtain JWT tokens",
    description="Authenticates with username and password, returning access and refresh JWT tokens alongside basic user profile information.",
    responses={
        200: OpenApiResponse(description="Tokens obtained successfully."),
        401: OpenApiResponse(description="Invalid credentials."),
    },
    tags=["Authentication"],
)
class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(
    summary="Refresh an expired access token",
    description="Submits a valid refresh token to obtain a fresh access token without re-entering credentials.",
    tags=["Authentication"],
)
class RefreshTokenView(TokenRefreshView):
    pass


@extend_schema(
    summary="Retrieve or update the authenticated user profile",
    description="GET: Returns the current user's profile.\nPUT / PATCH: Updates permitted profile fields (first_name, last_name, email). Role and privileges cannot be changed.",
    responses={
        200: OpenApiResponse(response=UserSerializer, description="Profile retrieved or updated successfully."),
        400: OpenApiResponse(description="Validation error on profile update."),
        401: OpenApiResponse(description="Authentication credentials were not provided or invalid."),
    },
    tags=["Authentication"],
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserProfileUpdateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Always return the full safe user representation in the response
        response_serializer = UserSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
