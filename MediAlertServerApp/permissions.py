from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                hasattr(request.user, 'profile') and 
                request.user.profile.user_type == 'ADMIN')

class IsSupervisor(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                hasattr(request.user, 'profile') and 
                request.user.profile.user_type == 'SUPERVISOR')

class IsProfessional(permissions.BasePermission):
    """
    Permite acceso solo a usuarios profesionales.
    """
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                hasattr(request.user, 'profile') and 
                request.user.profile.user_type == 'PROFESSIONAL')
    
class IsPatient(permissions.BasePermission):
    """
    Permite acceso solo a usuarios pacientes.
    """
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                hasattr(request.user, 'profile') and 
                request.user.profile.user_type == 'PATIENT')

class IsProfessionalOrSupervisorOrAdmin(permissions.BasePermission):
    """
    Permite acceso a profesionales, supervisores o administradores.
    """
    def has_permission(self, request, view):
        user_type = getattr(request.user.profile, 'user_type', None)
        return user_type in ['PROFESSIONAL', 'SUPERVISOR', 'ADMIN']

