from django.db.models import Q
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse

from accounts.models import User
from .models import Ticket
from .serializers import (
    TicketSerializer,
    TicketAssignSerializer,
    TicketStatusUpdateSerializer,
)
from .permissions import IsTicketParticipantOrStaff, IsManagerOrAdmin


class TicketPagination(PageNumberPagination):
    """
    Standard pagination for ticket list queries.
    Default page size is 10, configurable up to 100 via ?page_size=.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema_view(
    list=extend_schema(
        summary="List accessible support tickets",
        description="Returns tickets according to role permissions. Customers only see tickets created for their own account. Agents see tickets assigned to them or unassigned in queue. Managers and Admins see all tickets.",
        parameters=[
            OpenApiParameter('status', str, description="Filter by status: OPEN, IN_PROGRESS, WAITING_FOR_CUSTOMER, RESOLVED, CLOSED"),
            OpenApiParameter('priority', str, description="Filter by priority: LOW, MEDIUM, HIGH, CRITICAL"),
            OpenApiParameter('category', str, description="Filter by category: DELIVERY, PAYMENT, REFUND, CANCELLATION, ACCOUNT, PRODUCT, OTHER"),
            OpenApiParameter('assigned_to', str, description="Filter by assigned user ID or 'unassigned'"),
            OpenApiParameter('customer', int, description="Filter by customer ID (Staff only)"),
            OpenApiParameter('search', str, description="Search ticket number, subject, or description"),
            OpenApiParameter('ordering', str, description="Sort results by created_at, updated_at, priority, status"),
        ],
        tags=["Tickets"],
    ),
    create=extend_schema(
        summary="Create a new support ticket",
        description="Customers create tickets for their own account. Staff can create a ticket on behalf of a customer by supplying customer_id.",
        request=TicketSerializer,
        responses={
            201: TicketSerializer,
            400: OpenApiResponse(description="Validation error (e.g. missing customer profile, invalid category/priority)."),
        },
        tags=["Tickets"],
    ),
    retrieve=extend_schema(
        summary="Retrieve ticket details",
        description="Fetches full details of a specific ticket. Customers can only access their own tickets. Agents can access assigned or unassigned tickets. Managers and Admins have full access.",
        responses={
            200: TicketSerializer,
            403: OpenApiResponse(description="Access forbidden."),
            404: OpenApiResponse(description="Ticket not found."),
        },
        tags=["Tickets"],
    ),
    update=extend_schema(
        summary="Update a support ticket",
        description="Updates ticket fields based on role permissions. Customers can update subject, description, and category while the ticket is not closed. Agents can update status and category on assigned tickets. Managers/Admins have full update permissions.",
        request=TicketSerializer,
        tags=["Tickets"],
    ),
    partial_update=extend_schema(
        summary="Partially update a support ticket",
        description="Partially updates allowed fields based on role permissions.",
        request=TicketSerializer,
        tags=["Tickets"],
    ),
    destroy=extend_schema(
        summary="Delete a ticket",
        description="Permanently deletes a ticket. Restricted strictly to Managers and Administrators. Customers and Agents receive 403 Forbidden.",
        responses={
            204: OpenApiResponse(description="Ticket deleted successfully."),
            403: OpenApiResponse(description="Permission denied."),
        },
        tags=["Tickets"],
    ),
)
class TicketViewSet(viewsets.ModelViewSet):
    """
    CRUD and workflow operations for Support Tickets.
    Enforces strict role-based data isolation, permissions, and status workflows.
    """
    serializer_class = TicketSerializer
    permission_classes = [IsTicketParticipantOrStaff]
    pagination_class = TicketPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['ticket_number', 'subject', 'description']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Ticket.objects.none()

        # 1. Base queryset isolation by role
        if user.role == User.Role.CUSTOMER:
            # Customers only ever see their own tickets
            qs = Ticket.objects.filter(customer__user=user)
        elif user.role == User.Role.AGENT:
            # Agents see tickets assigned to them OR unassigned in queue
            qs = Ticket.objects.filter(Q(assigned_to=user) | Q(assigned_to__isnull=True))
        else:
            # Managers and Admins oversee all tickets
            qs = Ticket.objects.all()

        qs = qs.select_related('customer', 'customer__user', 'assigned_to')

        # 2. Query parameter filters
        params = self.request.query_params

        status_param = params.get('status')
        if status_param and status_param in Ticket.Status.values:
            qs = qs.filter(status=status_param)

        priority_param = params.get('priority')
        if priority_param and priority_param in Ticket.Priority.values:
            qs = qs.filter(priority=priority_param)

        category_param = params.get('category')
        if category_param and category_param in Ticket.Category.values:
            qs = qs.filter(category=category_param)

        assigned_to_param = params.get('assigned_to')
        if assigned_to_param:
            if assigned_to_param.lower() == 'unassigned':
                qs = qs.filter(assigned_to__isnull=True)
            elif assigned_to_param.isdigit():
                qs = qs.filter(assigned_to_id=int(assigned_to_param))

        customer_param = params.get('customer')
        if customer_param and customer_param.isdigit():
            qs = qs.filter(customer_id=int(customer_param))

        return qs

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role not in [User.Role.ADMIN, User.Role.MANAGER]:
            return Response(
                {'detail': 'Only Managers and Administrators are permitted to delete tickets.'},
                status=status.HTTP_403_FORBIDDEN
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Assign ticket to a support agent",
        description="Assigns or unassigns a ticket. Restricted to Managers and Administrators.",
        request=TicketAssignSerializer,
        responses={
            200: TicketSerializer,
            400: OpenApiResponse(description="Invalid agent user ID."),
            403: OpenApiResponse(description="Forbidden."),
        },
        tags=["Ticket Workflows"],
    )
    @action(detail=True, methods=['post'], permission_classes=[IsManagerOrAdmin])
    def assign(self, request, pk=None):
        ticket = self.get_object()
        serializer = TicketAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assigned_user = serializer.validated_data['assigned_to_id']
        ticket.assigned_to = assigned_user
        ticket.save()
        output = TicketSerializer(ticket, context={'request': request})
        return Response(output.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update ticket status",
        description="Updates ticket status through workflow transition. Allowed for assigned Agents, Managers, and Admins.",
        request=TicketStatusUpdateSerializer,
        responses={
            200: TicketSerializer,
            403: OpenApiResponse(description="Forbidden."),
        },
        tags=["Ticket Workflows"],
    )
    @action(detail=True, methods=['post'])
    def status(self, request, pk=None):
        ticket = self.get_object()
        if request.user.role == User.Role.CUSTOMER:
            return Response(
                {'detail': 'Customers cannot directly alter ticket status.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = TicketStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket.status = serializer.validated_data['status']
        ticket.save()
        output = TicketSerializer(ticket, context={'request': request})
        return Response(output.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Resolve ticket",
        description="Marks ticket as RESOLVED and records resolved_at timestamp. Accessible to assigned Agents, Managers, and Admins.",
        responses={200: TicketSerializer, 403: OpenApiResponse(description="Forbidden.")},
        tags=["Ticket Workflows"],
    )
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        ticket = self.get_object()
        if request.user.role == User.Role.CUSTOMER:
            return Response(
                {'detail': 'Customers cannot mark tickets as resolved directly.'},
                status=status.HTTP_403_FORBIDDEN
            )
        ticket.status = Ticket.Status.RESOLVED
        ticket.save()
        output = TicketSerializer(ticket, context={'request': request})
        return Response(output.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Close ticket",
        description="Marks ticket as CLOSED. Customers can close their own tickets; staff can close any accessible ticket.",
        responses={200: TicketSerializer},
        tags=["Ticket Workflows"],
    )
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        ticket = self.get_object()
        ticket.status = Ticket.Status.CLOSED
        ticket.save()
        output = TicketSerializer(ticket, context={'request': request})
        return Response(output.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Reopen ticket",
        description="Reopens a resolved or closed ticket to OPEN status and clears the resolved_at timestamp.",
        responses={200: TicketSerializer},
        tags=["Ticket Workflows"],
    )
    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        ticket = self.get_object()
        ticket.status = Ticket.Status.OPEN
        ticket.save()
        output = TicketSerializer(ticket, context={'request': request})
        return Response(output.data, status=status.HTTP_200_OK)
