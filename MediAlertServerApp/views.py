import csv
import json
from datetime import datetime, timedelta
from rest_framework import generics, permissions, viewsets, status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.permissions import BasePermission, IsAuthenticated, DjangoModelPermissions
from rest_framework.decorators import permission_classes, action
from django.db.models import Count, F, Q
from django.db.models import Count, Avg, Max, Min
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from .models import Medicamento, Recordatorio, RegistroToma, AdverseEffect, AlertNotification
from .serializers import UserSerializer, UserProfileSerializer, RegisterSerializer, MedicamentoSerializer, RecordatorioSerializer, RegistroTomaSerializer, AdverseEffectSerializer, AlertNotificationSerializer
from .services import NotificationService
from .report_generator import ReportGenerator
from .permissions import IsProfessional


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Los profesionales pueden ver todos los usuarios
        # Los pacientes solo pueden verse a sí mismos
        if hasattr(self.request.user, 'profile') and self.request.user.profile.user_type == 'PROFESSIONAL':
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Endpoint para obtener el perfil del usuario actual"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
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

class MedicamentoViewSet(viewsets.ModelViewSet):
    serializer_class = MedicamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
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

class RegistroTomaViewSet(viewsets.ModelViewSet):
    serializer_class = RegistroTomaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RegistroToma.objects.filter(medicamento=self.request.user)

    def perform_create(self, serializer):
        serializer.save()
    
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
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user

class CanManageReports(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('farmacovigilancia.manage_reports')

class AdverseEffectViewSet(viewsets.ModelViewSet):
    serializer_class = AdverseEffectSerializer
    
    def get_queryset(self):
        # Los profesionales pueden ver todos los efectos adversos
        # Los pacientes solo pueden ver los suyos
        if hasattr(self.request.user, 'profile') and self.request.user.profile.user_type == 'PROFESSIONAL':
            return AdverseEffect.objects.all()
        return AdverseEffect.objects.filter(patient=self.request.user)
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        elif self.action == 'mark_as_reviewed':
            return [IsAuthenticated(), IsProfessional()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        adverse_effect = serializer.save(patient=self.request.user)
        # Crear notificación después de guardar el efecto adverso
        NotificationService.create_alert(adverse_effect)

    @action(detail=True, methods=['post'])
    def mark_as_reviewed(self, request, pk=None):
        adverse_effect = self.get_object()
        adverse_effect.status = 'REVIEWED'
        adverse_effect.save()
        return Response({'status': 'reviewed'})

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
    permission_classes = [IsAuthenticated, IsProfessional]

    def get_permissions(self):
        """
        Verificar permisos específicos para cada endpoint
        """
        if self.action in ['statistics', 'medication_statistics', 'trends']:
            # Solo requiere ser profesional
            return [IsAuthenticated(), IsProfessional()]
        else:
            # Requiere permiso específico para gestionar reportes
            return [IsAuthenticated(), IsProfessional(), 
                   DjangoModelPermissions()]

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
                'medication__nombre'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:5],
            
            'by_severity': AdverseEffect.objects.values(
                'medication__nombre', 'severity'
            ).annotate(
                count=Count('id')
            ).order_by('medication__nombre', '-count')
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
        return Response({
            'pending': AdverseEffect.objects.filter(
                status='PENDING'
            ).count(),
            
            'urgent_pending': AdverseEffect.objects.filter(
                status='PENDING',
                severity__in=['GRAVE', 'MORTAL']
            ).count(),
            
            'recent_pending': AdverseEffectSerializer(
                AdverseEffect.objects.filter(
                    status='PENDING'
                ).order_by('-reported_at')[:5],
                many=True
            ).data
        })

    @action(detail=False, methods=['get'])
    def filtered_reports(self, request):
        queryset = AdverseEffect.objects.all()
        
        severity = request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
            
        medication = request.query_params.get('medication')
        if medication:
            queryset = queryset.filter(medication__nombre__icontains=medication)
            
        date_from = request.query_params.get('from')
        if date_from:
            queryset = queryset.filter(reported_at__gte=date_from)
            
        date_to = request.query_params.get('to')
        if date_to:
            queryset = queryset.filter(reported_at__lte=date_to)

        return Response({
            'count': queryset.count(),
            'results': AdverseEffectSerializer(
                queryset.order_by('-reported_at')[:20],
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
            severe_cases=Count('id', filter=Q(severity__in=['GRAVE', 'MORTAL'])),
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
            severe_cases=Count('id', filter=Q(severity__in=['GRAVE', 'MORTAL'])),
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
            'severe_cases': queryset.filter(severity__in=['GRAVE', 'MORTAL']).count(),
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