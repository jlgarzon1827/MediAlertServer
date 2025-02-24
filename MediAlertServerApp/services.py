from django.contrib.auth.models import User
from django.utils import timezone
from .models import AlertNotification, AdverseEffect

class NotificationService:
    @staticmethod
    def create_alert(adverse_effect):
        # Determinar la prioridad basada en la severidad
        priority_map = {
            'LEVE': 'LOW',
            'MODERADA': 'MEDIUM',
            'GRAVE': 'HIGH',
            'MORTAL': 'URGENT'
        }
        
        priority = priority_map.get(adverse_effect.severity, 'MEDIUM')
        
        # Crear notificación para profesionales de salud
        professionals = User.objects.filter(groups__name='HealthProfessionals')
        
        for professional in professionals:
            AlertNotification.objects.create(
                adverse_effect=adverse_effect,
                recipient=professional,
                title=f'Nuevo reporte de efecto adverso - {adverse_effect.medication.nombre}',
                message=f'Se ha reportado un efecto adverso {adverse_effect.severity.lower()} para el medicamento {adverse_effect.medication.nombre}',
                priority=priority
            )
