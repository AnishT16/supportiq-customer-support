from rest_framework import permissions
from accounts.models import User


class IsCustomerOwnerOrStaff(permissions.BasePermission):
    """
    Object-level permission for Customer records:
    - CUSTOMER: Can only read/update their own customer profile. Cannot delete.
    - AGENT: Can read and update any customer profile for support purposes. Cannot delete.
    - MANAGER: Can read, update, and delete customer profiles.
    - ADMIN: Full access (read, update, delete).
    """

    def has_permission(self, request, view):
        # All endpoints require authentication
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Admins and Managers have full object-level access
        if request.user.role in [User.Role.ADMIN, User.Role.MANAGER]:
            return True

        # Agents can inspect and edit customer info, but cannot delete customer records
        if request.user.role == User.Role.AGENT:
            return request.method not in ['DELETE']

        # Customers can only access their own profile and cannot delete it
        if request.user.role == User.Role.CUSTOMER:
            if request.method in ['DELETE']:
                return False
            return obj.user == request.user

        return False
