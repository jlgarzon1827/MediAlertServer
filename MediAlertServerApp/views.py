import csv
import json
from datetime import datetime, timedelta
from rest_framework import generics, permissions, viewsets, status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.permissions import BasePermission, IsAuthenticated, DjangoModelPermissions
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, F, Q
from django.db.models import Count, Avg, Max, Min
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from .models import DispositivoUsuario, MedicamentoMaestro, Medicamento, Recordatorio, RegistroToma, AdverseEffect, AlertNotification, Institution, UserProfile
from .serializers import UserSerializer, CombinedProfileSerializer, DispositivoUsuarioSerializer, \
    RegisterSerializer, MedicamentoMaestroSerializer, MedicamentoSerializer, RecordatorioSerializer, RegistroTomaSerializer, \
    AdverseEffectSerializer, AlertNotificationSerializer, InstitutionSerializer
from .services import FirebaseService
from .report_generator import ReportGenerator
from .permissions import IsProfessional, IsAdmin, IsSupervisor, IsSupervisorOrReadOnly, IsPatient, IsProfessionalOrSupervisorOrAdmin

class InstitutionViewSet(viewsets.ModelViewSet):
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAdmin() | IsSupervisor()]

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        elif self.action == 'assign_permissions':
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = User.objects.all()
        
        user_type = self.request.GET.get('user_type')
        if user_type:
            if user_type == 'PROFESSIONAL':
                queryset = queryset.filter(profile__user_type='PROFESSIONAL')
        
        # Resto de la lógica para filtrar según el usuario autenticado
        if hasattr(self.request.user, 'profile') and self.request.user.profile.user_type in ['ADMIN', 'SUPERVISOR']:
            return queryset
        # Los pacientes solo pueden verse a sí mismos
        return queryset.filter(id=self.request.user.id)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Endpoint para obtener el perfil del usuario actual y sus permisos"""
        serializer = self.get_serializer(request.user)
        permissions = list(request.user.get_all_permissions())
        data = serializer.data
        data['permissions'] = permissions
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def accept_data_protection(self, request):
        """Endpoint para aceptar la política de protección de datos"""
        try:
            profile = request.user.profile
            if not profile.data_protection_accepted:
                profile.data_protection_accepted = True
                profile.data_protection_accepted_at = timezone.now()
                profile.save()
                
                # Actualiza el serializador para incluir los nuevos campos
                return Response({
                    'status': 'policy_accepted',
                    'data_protection_accepted': profile.data_protection_accepted,
                    'data_protection_accepted_at': profile.data_protection_accepted_at
                })
            return Response({'status': 'policy_already_accepted'})
            
        except UserProfile.DoesNotExist:
            return Response({'error': 'Perfil de usuario no encontrado'}, 
                          status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Endpoint para actualizar el perfil del usuario actual"""
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsProfessional])
    def set_professional(self, request, pk=None):
        """Convertir un usuario en profesional (solo para profesionales)"""
        try:
            user = User.objects.get(pk=pk)
            user.profile.user_type = 'PROFESSIONAL'
            user.profile.save()
            
            # Añadir al grupo de profesionales si existe
            professional_group, created = Group.objects.get_or_create(name='HealthProfessionals')
            user.groups.add(professional_group)
            
            return Response({'status': 'user set as professional'})
        except User.DoesNotExist:
            return Response({'error': 'user not found'}, status=status.HTTP_404_NOT_FOUND)
        
    @action(detail=False, methods=['get'])
    def permissions(self, request):
        """Obtener los permisos del usuario actual"""
        user = request.user
        permissions = list(user.get_all_permissions())
        
        # Información adicional sobre el usuario
        user_info = {
            'is_professional': user.profile.user_type == 'PROFESSIONAL',
            'groups': list(user.groups.values_list('name', flat=True)),
            'permissions': permissions
        }
        
        return Response(user_info)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def assign_permissions(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
            permission_codename = request.data.get('permission_codename')
            
            # Assign permission to the user
            from django.contrib.auth.models import Permission
            permission = Permission.objects.get(codename=permission_codename)
            user.user_permissions.add(permission)
            
            return Response({'status': f'Permission {permission_codename} assigned to user {user.username}'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Permission.DoesNotExist:
            return Response({'error': 'Permission not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def set_role(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
            role = request.data.get('role')
            
            if role in ['ADMIN', 'SUPERVISOR', 'PROFESSIONAL', 'PATIENT']:
                user.profile.user_type = role
                user.profile.save()
                
                # Añadir o remover del grupo correspondiente
                if role == 'ADMIN':
                    admin_group, _ = Group.objects.get_or_create(name='Admins')
                    user.groups.clear()
                    user.groups.add(admin_group)
                elif role == 'SUPERVISOR':
                    supervisor_group, _ = Group.objects.get_or_create(name='Supervisors')
                    user.groups.clear()
                    user.groups.add(supervisor_group)
                elif role == 'PROFESSIONAL':
                    professional_group, _ = Group.objects.get_or_create(name='HealthProfessionals')
                    user.groups.clear()
                    user.groups.add(professional_group)
                elif role == 'PATIENT':
                    patients_group, _ = Group.objects.get_or_create(name='Patients')
                    user.groups.clear()
                    user.groups.add(patients_group)
                
                return Response({'status': 'Role updated'})
            return Response({'error': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
class DispositivoUsuarioViewSet(viewsets.ModelViewSet):
    serializer_class = DispositivoUsuarioSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DispositivoUsuario.objects.filter(usuario=self.request.user)
    
    def perform_create(self, serializer):
        # Si ya existe un dispositivo con este token, actualizarlo
        token = self.request.data.get('token')
        try:
            dispositivo = DispositivoUsuario.objects.get(token=token)
            dispositivo.usuario = self.request.user
            dispositivo.nombre_dispositivo = self.request.data.get('nombre_dispositivo', dispositivo.nombre_dispositivo)
            dispositivo.modelo = self.request.data.get('modelo', dispositivo.modelo)
            dispositivo.sistema_operativo = self.request.data.get('sistema_operativo', dispositivo.sistema_operativo)
            dispositivo.version_app = self.request.data.get('version_app', dispositivo.version_app)
            dispositivo.activo = True
            dispositivo.save()
        except DispositivoUsuario.DoesNotExist:
            serializer.save(usuario=self.request.user)
    
    @action(detail=False, methods=['post'])
    def register_token(self, request):
        """Endpoint simplificado para registrar token FCM"""
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Actualizar o crear dispositivo
        dispositivo, created = DispositivoUsuario.objects.update_or_create(
            token=token,
            defaults={
                'usuario': request.user,
                'nombre_dispositivo': request.data.get('device_name'),
                'modelo': request.data.get('model'),
                'sistema_operativo': request.data.get('os'),
                'version_app': request.data.get('app_version'),
                'activo': True
            }
        )
        
        return Response({'status': 'token registered', 'created': created})
    
    @action(detail=False, methods=['post'])
    def test_notification(self, request):
        """Enviar notificación de prueba al dispositivo actual"""
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Enviar notificación de prueba
        success = FirebaseService.send_notification(
            token=token,
            title='Notificación de prueba',
            body='Esta es una notificación de prueba de MediAlert',
            data={'type': 'test'}
        )
        
        if success:
            return Response({'status': 'notification sent'})
        return Response({'error': 'Error al enviar notificación'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MedicamentoMaestroViewSet(viewsets.ModelViewSet):
    serializer_class = MedicamentoMaestroSerializer
    permission_classes = [IsSupervisorOrReadOnly]
    queryset = MedicamentoMaestro.objects.all()

class MedicamentoViewSet(viewsets.ModelViewSet):
    serializer_class = MedicamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.profile.user_type == 'PROFESSIONAL':
            return Medicamento.objects.all()
        return Medicamento.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

class RecordatorioViewSet(viewsets.ModelViewSet):
    serializer_class = RecordatorioSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Recordatorio.objects.filter(usuario=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        recordatorio = self.get_object()
        recordatorio.activo = not recordatorio.activo
        recordatorio.save()
        return Response({'status': 'success', 'active': recordatorio.activo})
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Obtener recordatorios para hoy"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            activo=True
        ).filter(
            # Sin fecha de fin o con fecha de fin posterior o igual a hoy
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=today)
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Obtener próximos recordatorios (próximas 24 horas)"""
        now = timezone.now()
        tomorrow = now + timedelta(days=1)
        
        # Obtener recordatorios activos
        queryset = self.get_queryset().filter(
            activo=True
        ).filter(
            # Sin fecha de fin o con fecha de fin posterior o igual a hoy
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=now.date())
        )
        
        # Filtrar por hora (próximas 24 horas)
        upcoming_reminders = []
        for reminder in queryset:
            # Crear datetime para hoy con la hora del recordatorio
            reminder_time_today = datetime.combine(now.date(), reminder.hora)
            reminder_datetime = timezone.make_aware(reminder_time_today)
            
            # Si la hora ya pasó hoy, usar mañana
            if reminder_datetime < now:
                reminder_time_tomorrow = datetime.combine(tomorrow.date(), reminder.hora)
                reminder_datetime = timezone.make_aware(reminder_time_tomorrow)
            
            # Si está dentro de las próximas 24 horas
            if reminder_datetime <= tomorrow:
                upcoming_reminders.append(reminder)
        
        serializer = self.get_serializer(upcoming_reminders, many=True)
        return Response(serializer.data)

class RegistroTomaViewSet(viewsets.ModelViewSet):
    serializer_class = RegistroTomaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return RegistroToma.objects.filter(recordatorio__usuario=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_date_range(self, request):
        """Obtener registros de toma por rango de fechas"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = self.get_queryset()
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_programada__date__gte=start_date)
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_programada__date__lte=end_date)
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Obtener estadísticas de tomas"""
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        # Obtener registros en el rango de fechas
        queryset = self.get_queryset().filter(fecha_programada__date__gte=start_date)
        
        # Calcular estadísticas
        total = queryset.count()
        tomados = queryset.filter(estado='TOMADO').count()
        omitidos = queryset.filter(estado='OMITIDO').count()
        pospuestos = queryset.filter(estado='POSPUESTO').count()
        
        adherencia = (tomados / total * 100) if total > 0 else 0
        
        return Response({
            'total': total,
            'tomados': tomados,
            'omitidos': omitidos,
            'pospuestos': pospuestos,
            'adherencia': round(adherencia, 2)
        })
    
    @action(detail=True, methods=['post'])
    def tomar(self, request, pk=None):
        """Marcar un medicamento como tomado"""
        registro = self.get_object()
        
        if registro.estado == 'TOMADO':
            return Response({'status': 'already taken'})
        
        registro.estado = 'TOMADO'
        registro.fecha_toma = timezone.now()
        registro.save()
        
        return Response({'status': 'success'})
    
    @action(detail=True, methods=['post'])
    def posponer(self, request, pk=None):
        """Posponer un recordatorio"""
        registro = self.get_object()
        minutos = int(request.data.get('minutos', 15))
        
        if registro.estado == 'TOMADO':
            return Response({'status': 'already taken'})
        
        # Crear un nuevo registro pospuesto
        nueva_fecha = registro.fecha_programada + timedelta(minutes=minutos)
        
        registro.estado = 'POSPUESTO'
        registro.save()
        
        nuevo_registro = RegistroToma.objects.create(
            recordatorio=registro.recordatorio,
            fecha_programada=nueva_fecha
        )
        
        return Response({
            'status': 'postponed',
            'new_registro_id': nuevo_registro.id,
            'new_time': nueva_fecha
        })
    
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer  # Usar el RegisterSerializer en lugar de UserSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()  # El RegisterSerializer ya manejaría los campos de profesional
        
        # Asignar al grupo de pacientes por defecto
        patients_group, _ = Group.objects.get_or_create(name='Patients')
        user.groups.add(patients_group)
        
        # Si es profesional, asignar al grupo de profesionales
        if hasattr(user, 'profile') and user.profile.user_type == 'PROFESSIONAL':
            professional_group, _ = Group.objects.get_or_create(name='HealthProfessionals')
            user.groups.add(professional_group)
        
        # Generar tokens (código existente)
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UserSerializer(user).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        })

class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CombinedProfileSerializer

    def get_object(self):
        return self.request.user

class AdverseEffectViewSet(viewsets.ModelViewSet):
    serializer_class = AdverseEffectSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        elif self.action in ['create']:
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update']:
            return [IsProfessional() | IsSupervisor() | IsAdmin()]
        elif self.action in ['assign_reviewer', 'revert_status', 'review_reclamation']:
            return [IsSupervisor()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.profile.user_type == 'ADMIN':
            return AdverseEffect.objects.all()
        elif self.request.user.profile.user_type == 'SUPERVISOR':
            return AdverseEffect.objects.filter(institution=self.request.user.profile.institution)
        elif self.request.user.profile.user_type == 'PROFESSIONAL':
            return AdverseEffect.objects.filter(reviewer=self.request.user, institution=self.request.user.profile.institution)
        return AdverseEffect.objects.filter(patient=self.request.user, institution=self.request.user.profile.institution)

    @action(detail=True, methods=['post'], permission_classes=[IsSupervisor])
    def assign_reviewer(self, request, pk=None):
        adverse_effect = self.get_object()
        reviewer_id = request.data.get('reviewer_id')
        
        try:
            reviewer = User.objects.get(pk=reviewer_id)
            if reviewer.profile.user_type == 'PROFESSIONAL':
                adverse_effect.reviewer = reviewer
                adverse_effect.status = 'ASSIGNED'
                adverse_effect.save()
                return Response({'status': 'Reviewer assigned successfully'})
            else:
                return Response({'error': 'User is not a professional'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'Reviewer not found'}, status=status.HTTP_404_NOT_FOUND)

    #Supervisor transitions
    @action(detail=True, methods=['post'], permission_classes=[IsSupervisor])
    def revert_status(self, request, pk=None):
        adverse_effect = self.get_object()

        if adverse_effect.status != 'APPROVED':
            return Response({'error': 'No se puede revertir en este estado'}, status=status.HTTP_400_BAD_REQUEST)

        revertion_reason = request.data.get('reason')
        if not revertion_reason:
            return Response({'error': 'Debe proporcionar un motivo para la reversión'}, status=status.HTTP_400_BAD_REQUEST)
        
        adverse_effect.revertion_reason = revertion_reason
        adverse_effect.status = 'IN_REVISION'
        adverse_effect.save()
        
        return Response({'status': 'Estado revertido', 'reason': revertion_reason})

    @action(detail=True, methods=['post'], permission_classes=[IsSupervisor])
    def approve_reclamation(self, request, pk=None):
        adverse_effect = self.get_object()

        if adverse_effect.status != 'RECLAIMED':
            return Response({'error': 'No se puede aprovar una reclamación en este estado'}, status=status.HTTP_400_BAD_REQUEST)

        adverse_effect.status = 'APPROVED'
        adverse_effect.save()
        return Response({'status': 'Reclamation accepted'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsSupervisor])
    def reject_reclamation(self, request, pk=None):
        adverse_effect = self.get_object()

        if adverse_effect.status != 'RECLAIMED':
            return Response({'error': 'No se puede rechazar la reclamación en este estado'}, status=status.HTTP_400_BAD_REQUEST)

        adverse_effect.status = 'REJECTED'
        adverse_effect.save()
        return Response({'status': 'Reclamation rejected'})

    #Professional transitions
    @action(detail=True, methods=['post'], permission_classes=[IsProfessional])
    def start_review(self, request, pk=None):
        adverse_effect = self.get_object()
        
        if adverse_effect.status != 'ASSIGNED':
            return Response({'error': 'No se puede iniciar la revisión en este estado'}, status=status.HTTP_400_BAD_REQUEST)
        
        adverse_effect.status = 'IN_REVISION'
        adverse_effect.save()
        return Response({'status': 'Revision initiated'})

    @action(detail=True, methods=['post'], permission_classes=[IsProfessional])
    def request_additional_info(self, request, pk=None):
        adverse_effect = self.get_object()

        if adverse_effect.status != 'IN_REVISION':
            return Response({'error': 'No se puede solicitar información adicional en este estado'}, status=status.HTTP_400_BAD_REQUEST)

        adverse_effect.status = 'PENDING_INFORMATION'
        adverse_effect.chat_active = True
        adverse_effect.save()
        return Response({'status': 'Additional info requested'})

    @action(detail=True, methods=['post'], permission_classes=[IsProfessional])
    def approve_report(self, request, pk=None):
        adverse_effect = self.get_object()

        if adverse_effect.status != 'IN_REVISION':
            return Response({'error': 'No se puede aprobar un reporte en este estado'}, status=status.HTTP_400_BAD_REQUEST)

        adverse_effect.status = 'APPROVED'
        adverse_effect.save()
        return Response({'status': 'Report approved'})

    @action(detail=True, methods=['post'], permission_classes=[IsProfessional])
    def reject_report(self, request, pk=None):
        adverse_effect = self.get_object()

        if adverse_effect.status != 'IN_REVISION':
            return Response({'error': 'No se puede rechazar un reporte en este estado'}, status=status.HTTP_400_BAD_REQUEST)

        adverse_effect.status = 'REJECTED'
        adverse_effect.save()
        return Response({'status': 'Report rejected'})

    #Patient transitions
    @action(detail=True, methods=['post'], permission_classes=[IsPatient])
    def start_reclamation(self, request, pk=None):
        adverse_effect = self.get_object()

        if adverse_effect.status != 'REJECTED':
            return Response({'error': 'No se puede iniciar la reclamación en este estado'}, status=status.HTTP_400_BAD_REQUEST)

        if adverse_effect.patient != request.user:
            return Response({'error': 'Solo el paciente puede iniciar la reclamación'}, status=status.HTTP_403_FORBIDDEN)

        reclamation_reason = request.data.get('reclamation_reason')
        if not reclamation_reason:
            return Response({'error': 'El motivo de la reclamación es obligatorio'}, status=status.HTTP_400_BAD_REQUEST)

        adverse_effect.reclamation_reason = reclamation_reason
        adverse_effect.status = 'RECLAIMED'
        adverse_effect.save()

        return Response({'status': 'Reclamación iniciada', 'reclamation_reason': reclamation_reason})


    @action(detail=True, methods=['post'], permission_classes=[IsPatient])
    def provide_additional_info(self, request, pk=None):
        adverse_effect = self.get_object()
        
        if adverse_effect.status != 'PENDING_INFORMATION':
            return Response({'error': 'No se puede proporcionar información adicional en este estado'}, status=status.HTTP_400_BAD_REQUEST)

        if adverse_effect.patient != request.user:
            return Response({'error': 'Solo el paciente puede proporcionar información adicional'}, status=status.HTTP_403_FORBIDDEN)

        # Procesar la información adicional aquí
        additional_info = request.data.get('additional_info')
        
        # Guardar la información adicional en la base de datos
        adverse_effect.additional_info = additional_info
        adverse_effect.status = 'IN_REVISION'
        adverse_effect.save()
        
        return Response({'status': 'Información adicional proporcionada'})

    @action(detail=True, methods=['post'], permission_classes=[IsSupervisor])
    def update_status(self, request, pk=None):
        adverse_effect = self.get_object()
        new_status = request.data.get('status')
        
        if new_status in ['CREATED', 'ASSIGNED', 'IN_REVISION', 'PENDING_INFORMATION', 'REJECTED', 'RECLAIMED', 'APPROVED']:
            adverse_effect.status = new_status
            adverse_effect.save()
            return Response({'status': f'Estado actualizado a {new_status}'})
        else:
            return Response({'error': 'Estado no válido'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def filtered_reports(self, request):
        queryset = self.get_queryset()
        
        filters = {}
        
        severity = request.query_params.get('severity')
        if severity:
            filters['severity'] = severity
        
        medication = request.query_params.get('medication')
        if medication:
            filters['medication__nombre__icontains'] = medication
        
        status = request.query_params.get('status')
        if status:
            filters['status__iexact'] = status

        type_param = request.query_params.get('type')
        if type_param:
            filters['type'] = type_param

        institution = request.query_params.get('institution')
        if institution:
            filters['institution__id'] = institution
        
        date_from = request.query_params.get('from')
        date_to = request.query_params.get('to')
        
        if date_from or date_to:
            date_filter = Q()
            if date_from:
                date_filter &= Q(reported_at__gte=date_from)
            if date_to:
                date_filter &= Q(reported_at__lte=date_to)
            
            queryset = queryset.filter(date_filter)
        
        queryset = queryset.filter(**filters).order_by('-reported_at')
        
        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(queryset, request)
        
        serializer = AdverseEffectSerializer(result_page, many=True)
        
        return paginator.get_paginated_response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_message(self, request, pk=None):
        adverse_effect = self.get_object()
        
        if adverse_effect.status != 'PENDING_INFORMATION':
            return Response({'error': 'Chat no disponible'}, status=400)
        
        user = request.user
        if user != adverse_effect.patient and user != adverse_effect.reviewer:
            return Response({'error': 'No autorizado'}, status=403)
        
        message = request.data.get('message')
        if not message:
            return Response({'error': 'Mensaje vacío'}, status=400)
        
        sender_role = 'patient' if user == adverse_effect.patient else 'professional'
        adverse_effect.chat_messages.append({
            'sender': sender_role,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        adverse_effect.save()
        
        return Response({'status': 'Mensaje añadido'})

    @action(detail=True, methods=['post'], permission_classes=[IsProfessional])
    def close_chat(self, request, pk=None):
        adverse_effect = self.get_object()
        
        if adverse_effect.status != 'PENDING_INFORMATION':
            return Response({'error': 'Chat no activo'}, status=400)
        
        # Añade mensaje de cierre
        adverse_effect.chat_messages.append({
            'sender': 'system',
            'message': 'Chat cerrado por profesional',
            'timestamp': datetime.now().isoformat()
        })
        
        adverse_effect.status = 'IN_REVISION'
        adverse_effect.chat_active = False
        adverse_effect.save()
        
        return Response({'status': 'Chat cerrado'})

class AlertNotificationViewSet(viewsets.ModelViewSet):
    serializer_class = AlertNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AlertNotification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.read_at = timezone.now()
        notification.save()
        return Response({'status': 'marked as read'})

    @action(detail=False, methods=['get'])
    def unread(self, request):
        unread_notifications = self.get_queryset().filter(read_at__isnull=True)
        serializer = self.get_serializer(unread_notifications, many=True)
        return Response(serializer.data)

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AdverseEffect.objects.all()

    def get_permissions(self):
        """
        Verificar permisos específicos para cada endpoint.
        """
        if self.action in ['statistics', 'medication_statistics', 'trends']:
            return [IsAuthenticated(), IsProfessionalOrSupervisorOrAdmin()]
        elif self.action in ['supervisor_view']:
            return [IsAuthenticated(), IsSupervisor()]
        else:
            return [IsAuthenticated()]
        
    @action(detail=False, methods=['get'])
    def supervisor_view(self, request):
        """
        Vista general de reportes para supervisores.
        """
        queryset = AdverseEffect.objects.all()

        # Aplicar filtros si existen
        filters = {}
        
        severity = request.query_params.get('severity')
        if severity:
            filters['severity'] = severity

        medication = request.query_params.get('medication')
        if medication:
            filters['medication__nombre__icontains'] = medication

        status = request.query_params.get('status')
        if status:
            filters['status__iexact'] = status

        reviewer = request.query_params.get('reviewer')
        if reviewer:
            if reviewer.lower() == 'null':
                filters['reviewer__isnull'] = True
            else:
                filters['reviewer'] = reviewer

        type_param = request.query_params.get('type')
        if type_param:
            filters['type'] = type_param

        date_from = request.query_params.get('from')
        date_to = request.query_params.get('to')
        
        if date_from or date_to:
            date_filter = Q()
            if date_from:
                date_filter &= Q(reported_at__gte=date_from)
            if date_to:
                date_filter &= Q(reported_at__lte=date_to)
            queryset = queryset.filter(date_filter)

        queryset = queryset.filter(**filters).order_by('-reported_at')

        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(queryset, request)
        
        serializer = AdverseEffectSerializer(result_page, many=True)
        
        return paginator.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        total_reports = AdverseEffect.objects.count()
        by_severity = AdverseEffect.objects.values('severity').annotate(count=Count('id'))
        by_type = AdverseEffect.objects.values('type').annotate(count=Count('id'))
        
        return Response({
            'total_reports': total_reports,
            'by_severity': by_severity,
            'by_type': by_type
        })

    @action(detail=False, methods=['get'])
    def medication_statistics(self, request):
        return Response({
            'most_reported': AdverseEffect.objects.values(
                'medication__medicamento_maestro__nombre'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:5],
            
            'by_severity': AdverseEffect.objects.values(
                'medication__medicamento_maestro__nombre', 'severity'
            ).annotate(
                count=Count('id')
            ).order_by('medication__medicamento_maestro__nombre', '-count')
        })

    @action(detail=False, methods=['get'])
    def trends(self, request):
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        return Response({
            'daily_reports': AdverseEffect.objects.filter(
                reported_at__gte=thirty_days_ago
            ).extra(
                select={'date': 'date(reported_at)'}
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date'),
            
            'severity_trend': AdverseEffect.objects.filter(
                reported_at__gte=thirty_days_ago
            ).values('severity').annotate(
                count=Count('id')
            )
        })

    @action(detail=False, methods=['get'])
    def pending_reviews(self, request):
        user = request.user

        queryset = AdverseEffect.objects.filter(status='IN_REVISION')
        if hasattr(user, 'profile') and user.profile.user_type == 'PROFESSIONAL':
            queryset = queryset.filter(reviewer=user)

        return Response({
            'pending': queryset.count(),
            'urgent_pending': queryset.filter(severity__in=['GRAVE', 'MUY_GRAVE']).count(),
            'recent_pending': AdverseEffectSerializer(
                queryset.order_by('-reported_at')[:5],
                many=True
            ).data
        })
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Exportar datos a CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="adverse_effects_{datetime.now().strftime("%Y%m%d")}.csv"'

        # Aplicar filtros si existen
        queryset = self._get_filtered_queryset(request)

        writer = csv.writer(response)
        writer.writerow(['Fecha', 'Medicamento', 'Severidad', 'Tipo', 'Descripción', 'Estado'])

        for effect in queryset:
            writer.writerow([
                effect.reported_at.strftime("%Y-%m-%d"),
                effect.medication.nombre,
                effect.severity,
                effect.type,
                effect.description,
                effect.status
            ])

        return response

    @action(detail=False, methods=['get'])
    def export_json(self, request):
        """Exportar datos a JSON"""
        queryset = self._get_filtered_queryset(request)
        serializer = AdverseEffectSerializer(queryset, many=True)

        response = HttpResponse(
            json.dumps(serializer.data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="adverse_effects_{datetime.now().strftime("%Y%m%d")}.json"'
        return response

    def _get_filtered_queryset(self, request):
        """Método auxiliar para aplicar filtros"""
        queryset = AdverseEffect.objects.all()
        
        # Filtros por fecha
        date_from = request.query_params.get('from')
        date_to = request.query_params.get('to')
        if date_from:
            queryset = queryset.filter(reported_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(reported_at__lte=date_to)

        # Filtros por severidad y tipo
        severity = request.query_params.get('severity')
        effect_type = request.query_params.get('type')
        if severity:
            queryset = queryset.filter(severity=severity)
        if effect_type:
            queryset = queryset.filter(type=effect_type)

        return queryset.order_by('-reported_at')

    @action(detail=False, methods=['get'])
    def analysis_report(self, request):
        """Análisis detallado de efectos adversos"""
        return Response({
            'severity_analysis': self._get_severity_analysis(),
            'medication_analysis': self._get_medication_analysis(),
            'temporal_analysis': self._get_temporal_analysis(),
            'type_analysis': self._get_type_analysis()
        })

    def _get_severity_analysis(self):
        """Análisis por severidad"""
        return AdverseEffect.objects.values('severity').annotate(
            count=Count('id'),
            percentage=Count('id') * 100.0 / AdverseEffect.objects.count(),
            avg_resolution_time=Avg('updated_at' - F('reported_at'))
        ).order_by('-count')

    def _get_medication_analysis(self):
        """Análisis por medicamento"""
        return AdverseEffect.objects.values(
            'medication__nombre'
        ).annotate(
            total_reports=Count('id'),
            severe_cases=Count('id', filter=Q(severity__in=['GRAVE', 'MUY_GRAVE'])),
            most_common_type=Max('type'),
            first_reported=Min('reported_at'),
            last_reported=Max('reported_at')
        ).order_by('-total_reports')

    def _get_temporal_analysis(self):
        """Análisis temporal"""
        return {
            'monthly': AdverseEffect.objects.annotate(
                month=TruncMonth('reported_at')
            ).values('month').annotate(
                count=Count('id')
            ).order_by('month'),
            
            'weekly': AdverseEffect.objects.annotate(
                week=TruncWeek('reported_at')
            ).values('week').annotate(
                count=Count('id')
            ).order_by('week')
        }

    def _get_type_analysis(self):
        """Análisis por tipo de efecto"""
        return AdverseEffect.objects.values('type').annotate(
            count=Count('id'),
            severe_cases=Count('id', filter=Q(severity__in=['GRAVE', 'MUY_GRAVE'])),
            medications_affected=Count('medication', distinct=True)
        ).order_by('-count')

    @action(detail=False, methods=['get'])
    def correlation_analysis(self, request):
        """Análisis de correlaciones"""
        return Response({
            'severity_by_age': self._get_severity_age_correlation(),
            'type_by_medication': self._get_type_medication_correlation(),
            'severity_by_route': self._get_severity_route_correlation()
        })

    def _get_severity_age_correlation(self):
        """Correlación entre severidad y edad del paciente"""
        return AdverseEffect.objects.values(
            'severity', 'patient__profile__age_range'
        ).annotate(
            count=Count('id')
        ).order_by('severity', 'patient__profile__age_range')

    def _get_type_medication_correlation(self):
        """Correlación entre tipo de efecto y medicamento"""
        return AdverseEffect.objects.values(
            'type', 'medication__nombre'
        ).annotate(
            count=Count('id')
        ).order_by('-count')

    def _get_severity_route_correlation(self):
        """Correlación entre severidad y vía de administración"""
        return AdverseEffect.objects.values(
            'severity', 'administration_route'
        ).annotate(
            count=Count('id')
        ).order_by('severity', '-count')

    @action(detail=False, methods=['get'])
    def generate_pdf_report(self, request):
        """Generar reporte PDF"""
        # Obtener datos filtrados
        queryset = self._get_filtered_queryset(request)
        
        # Preparar datos para el reporte
        report_data = {
            'total_reports': queryset.count(),
            'severe_cases': queryset.filter(severity__in=['GRAVE', 'MUY_GRAVE']).count(),
            'pending_cases': queryset.filter(status='PENDING').count(),
            'effects': [{
                'medication': effect.medication.nombre,
                'severity': effect.severity,
                'type': effect.type,
                'reported_at': effect.reported_at.strftime('%Y-%m-%d')
            } for effect in queryset]
        }
        
        # Generar PDF
        generator = ReportGenerator()
        pdf = generator.generate_adverse_effects_report(
            report_data,
            filters=dict(request.query_params)
        )
        
        # Preparar respuesta
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="adverse_effects_report_{datetime.now().strftime("%Y%m%d")}.pdf"'
        response.write(pdf)
        
        return response