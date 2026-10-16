from rest_framework import viewsets, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from accounts.models import User
from .models import Customer
from .serializers import CustomerSerializer
from .permissions import IsCustomerOwnerOrStaff


@extend_schema_view(
    list=extend_schema(
        summary="List customer records",
        description="Returns customer records accessible to the authenticated user. Customers only see their own profile. Agents, Managers, and Admins can view all customers.",
        responses={200: CustomerSerializer(many=True)},
        tags=["Customers"],
    ),
    create=extend_schema(
        summary="Create customer profile",
        description="Creates a new customer profile. Customers can create their own profile. Staff/Managers can create customer profiles for existing users by providing user_id.",
        request=CustomerSerializer,
        responses={
            201: CustomerSerializer,
            400: OpenApiResponse(description="Validation error (e.g. duplicate email, profile already exists, or invalid user ID)."),
        },
        tags=["Customers"],
    ),
    retrieve=extend_schema(
        summary="Retrieve customer details",
        description="Retrieves a specific customer profile by ID. Customers can only view their own profile. Agents, Managers, and Admins can view any customer.",
        responses={
            200: CustomerSerializer,
            403: OpenApiResponse(description="Access forbidden (unauthorized customer)."),
            404: OpenApiResponse(description="Customer not found."),
        },
        tags=["Customers"],
    ),
    update=extend_schema(
        summary="Update customer profile",
        description="Updates all fields of an existing customer profile. Ownership cannot be reassigned.",
        request=CustomerSerializer,
        responses={
            200: CustomerSerializer,
            400: OpenApiResponse(description="Validation error."),
            403: OpenApiResponse(description="Forbidden."),
        },
        tags=["Customers"],
    ),
    partial_update=extend_schema(
        summary="Partially update customer profile",
        description="Partially updates fields of an existing customer profile. Ownership cannot be reassigned.",
        request=CustomerSerializer,
        responses={
            200: CustomerSerializer,
            400: OpenApiResponse(description="Validation error."),
            403: OpenApiResponse(description="Forbidden."),
        },
        tags=["Customers"],
    ),
    destroy=extend_schema(
        summary="Delete customer profile",
        description="Permanently deletes a customer profile. Restricted to Managers and Administrators. Customers and Agents are prohibited from deleting customer records.",
        responses={
            204: OpenApiResponse(description="Customer deleted successfully."),
            403: OpenApiResponse(description="Permission denied. Only Managers and Admins can delete customer records."),
        },
        tags=["Customers"],
    ),
)
class CustomerViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Customer management.
    Enforces role-based data filtering and object-level permissions.
    """
    serializer_class = CustomerSerializer
    permission_classes = [IsCustomerOwnerOrStaff]

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Customer.objects.none()

        # Customers can only see their own customer profile
        if user.role == User.Role.CUSTOMER:
            return Customer.objects.filter(user=user)

        # Agents, Managers, and Admins can query all customers
        return Customer.objects.all().select_related('user')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Explicit check: Only Managers and Admins are permitted to delete customer records
        if request.user.role not in [User.Role.ADMIN, User.Role.MANAGER]:
            return Response(
                {'detail': 'You do not have permission to delete customer records. Manager or Admin privileges required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
