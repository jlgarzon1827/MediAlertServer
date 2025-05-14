from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import DispositivoUsuario, AlertNotification, Recordatorio, RegistroToma
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import os
import json

# Inicializar Firebase Admin SDK
cred_path = os.path.join(settings.BASE_DIR, 'firebase-credentials.json')
if os.path.exists(cred_path):
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

class RecordatorioService:
    @staticmethod
    def generate_upcoming_registros(days=7):
        """
        Genera registros de toma para los próximos días
        basados en los recordatorios activos
        """
        today = timezone.now().date()
        end_date = today + timedelta(days=days)
        
        # Obtener todos los recordatorios activos
        recordatorios = Recordatorio.objects.filter(
            activo=True
        ).filter(
            # Sin fecha de fin o con fecha de fin posterior o igual a hoy
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=today)
        )
        
        registros_creados = 0
        
        for recordatorio in recordatorios:
            current_date = today
            
            while current_date <= end_date:
                # Verificar si el recordatorio aplica para este día
                if recordatorio.frecuencia == 'DAILY' or (
                    recordatorio.frecuencia == 'WEEKLY' and 
                    str(current_date.weekday() + 1) in (recordatorio.dias_semana or '').split(',')
                ):
                    # Crear datetime combinando fecha y hora
                    fecha_programada = datetime.combine(current_date, recordatorio.hora)
                    fecha_programada = timezone.make_aware(fecha_programada)
                    
                    # Verificar si ya existe un registro para esta fecha y recordatorio
                    registro_exists = RegistroToma.objects.filter(
                        recordatorio=recordatorio,
                        fecha_programada=fecha_programada
                    ).exists()
                    
                    if not registro_exists:
                        RegistroToma.objects.create(
                            recordatorio=recordatorio,
                            fecha_programada=fecha_programada
                        )
                        registros_creados += 1
                
                current_date += timedelta(days=1)
        
        return registros_creados

class NotificationService:
    @staticmethod
    def create_alert(adverse_effect):
        # Determinar la prioridad basada en la severidad
        priority_map = {
            'LEVE': 'LOW',
            'MODERADA': 'MEDIUM',
            'GRAVE': 'HIGH',
            'MUY_GRAVE': 'URGENT'
        }
        
        priority = priority_map.get(adverse_effect.severity, 'MEDIUM')
        
        # Crear notificación para profesionales de salud
        professionals = User.objects.filter(groups__name='HealthProfessionals')
        
        for professional in professionals:
            AlertNotification.objects.create(
                adverse_effect=adverse_effect,
                recipient=professional,
                title=f'Nuevo reporte de efecto adverso - {adverse_effect.medication.medicamento_maestro.nombre}',
                message=f'Se ha reportado un efecto adverso {adverse_effect.severity.lower()} para el medicamento {adverse_effect.medication.nombre}',
                priority=priority
            )

class FirebaseService:
    @staticmethod
    def send_notification(token, title, body, data=None):
        """
        Envía una notificación push a un dispositivo específico
        
        Args:
            token (str): Token FCM del dispositivo
            title (str): Título de la notificación
            body (str): Cuerpo del mensaje
            data (dict, optional): Datos adicionales para la notificación
        
        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        try:
            # Configurar mensaje
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        priority='high',
                        channel_id='medication_reminders'
                    )
                )
            )
            
            # Enviar mensaje
            response = messaging.send(message)
            return True
        except Exception as e:
            print(f"Error al enviar notificación: {e}")
            return False
    
    @staticmethod
    def send_multicast(tokens, title, body, data=None):
        """
        Envía notificaciones a múltiples dispositivos
        
        Args:
            tokens (list): Lista de tokens FCM
            title (str): Título de la notificación
            body (str): Cuerpo del mensaje
            data (dict, optional): Datos adicionales para la notificación
        
        Returns:
            dict: Resultado del envío con éxitos y fallos
        """
        try:
            # Configurar mensaje
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                tokens=tokens,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        priority='high',
                        channel_id='medication_reminders'
                    )
                )
            )
            
            # Enviar mensaje
            response = messaging.send_multicast(message)
            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count
            }
        except Exception as e:
            print(f"Error al enviar notificaciones multicast: {e}")
            return {'success_count': 0, 'failure_count': len(tokens)}

class ReminderNotificationService:
    @staticmethod
    def send_medication_reminders(minutes_before=15):
        """
        Envía recordatorios de medicamentos a los usuarios
        
        Args:
            minutes_before (int): Minutos antes de la hora programada para enviar el recordatorio
        
        Returns:
            dict: Estadísticas de envío
        """
        now = timezone.now()
        target_time = now + timedelta(minutes=minutes_before)
        
        # Obtener registros de toma programados para el momento objetivo
        registros = RegistroToma.objects.filter(
            fecha_programada__year=target_time.year,
            fecha_programada__month=target_time.month,
            fecha_programada__day=target_time.day,
            fecha_programada__hour=target_time.hour,
            fecha_programada__minute=target_time.minute,
            estado='OMITIDO'  # Solo los que aún no se han tomado
        )
        
        stats = {
            'total': registros.count(),
            'sent': 0,
            'failed': 0,
            'no_device': 0
        }
        
        for registro in registros:
            # Obtener dispositivos activos del usuario
            dispositivos = DispositivoUsuario.objects.filter(
                usuario=registro.recordatorio.usuario,
                activo=True
            )
            
            if not dispositivos.exists():
                stats['no_device'] += 1
                continue
            
            # Preparar datos para la notificación
            medicamento = registro.recordatorio.medicamento
            title = f"Recordatorio: {medicamento.medicamento_maestro.nombre}"
            body = f"Es hora de tomar {registro.recordatorio.dosis} de {medicamento.medicamento_maestro.nombre}"
            data = {
                'type': 'medication_reminder',
                'registro_id': str(registro.id),
                'medicamento_id': str(medicamento.id),
                'medicamento_nombre': medicamento.medicamento_maestro.nombre,
                'dosis': registro.recordatorio.dosis
            }
            
            # Enviar a todos los dispositivos del usuario
            tokens = [d.token for d in dispositivos]
            result = FirebaseService.send_multicast(tokens, title, body, data)
            
            stats['sent'] += result.get('success_count', 0)
            stats['failed'] += result.get('failure_count', 0)
        
        return stats
