from rest_framework import permissions
from accounts.models import User
from .models import Ticket


class IsTicketParticipantOrStaff(permissions.BasePermission):
    """
    Object-level permission for Tickets:
    - CUSTOMER: Can only read/update their own tickets. Cannot delete. Cannot edit closed tickets.
    - AGENT: Can read tickets assigned to them or unassigned in queue. Can update tickets assigned to them. Cannot delete.
    - MANAGER: Full read/write/delete access. Can assign tickets.
    - ADMIN: Full read/write/delete access.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Admins and Managers have full object-level permissions
        if user.role in [User.Role.ADMIN, User.Role.MANAGER]:
            return True

        # Agents can inspect unassigned tickets or tickets assigned to them
        if user.role == User.Role.AGENT:
            if request.method in permissions.SAFE_METHODS:
                return obj.assigned_to == user or obj.assigned_to is None
            if request.method in ['PUT', 'PATCH', 'POST']:
                # Agent can update or trigger actions on tickets explicitly assigned to them
                return obj.assigned_to == user
            # Agents cannot delete tickets
            return False

        # Customers can only view/update their own tickets
        if user.role == User.Role.CUSTOMER:
            if request.method in ['DELETE']:
                return False
            # Check ownership
            if obj.customer.user != user:
                return False
            # Customer cannot edit a closed ticket
            if request.method in ['PUT', 'PATCH'] and obj.status == Ticket.Status.CLOSED:
                return False
            return True

        return False


class IsManagerOrAdmin(permissions.BasePermission):
    """
    Permission restricted strictly to Managers and Administrators.
    Used for ticket assignment and privileged management operations.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in [User.Role.ADMIN, User.Role.MANAGER]
        )
