from rest_framework import permissions

class IsProfessional(permissions.BasePermission):
    """
    Permite acceso solo a usuarios profesionales.
    """
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                hasattr(request.user, 'profile') and 
                request.user.profile.user_type == 'PROFESSIONAL')
