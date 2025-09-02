from rest_framework.permissions import BasePermission


class IsSelfOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.id == request.user.id


class IsOwnerProfileOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user_id == request.user.id
