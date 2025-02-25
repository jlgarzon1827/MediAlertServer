from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from MediAlertServerApp.models import AdverseEffect, Medicamento

class Command(BaseCommand):
    help = 'Configura los grupos y permisos iniciales'

    def handle(self, *args, **options):
        # Crear grupo para profesionales de la salud
        health_professionals, created = Group.objects.get_or_create(name='HealthProfessionals')
        if created:
            self.stdout.write(self.style.SUCCESS('Grupo "HealthProfessionals" creado'))
        
        # Crear grupo para pacientes
        patients, created = Group.objects.get_or_create(name='Patients')
        if created:
            self.stdout.write(self.style.SUCCESS('Grupo "Patients" creado'))
        
        # Obtener content types
        adverse_effect_ct = ContentType.objects.get_for_model(AdverseEffect)
        medication_ct = ContentType.objects.get_for_model(Medicamento)
        
        # Permisos para profesionales
        professional_permissions = []
        
        # Intentar obtener permisos para AdverseEffect
        for codename in ['view_adverseeffect', 'change_adverseeffect']:
            try:
                perm = Permission.objects.get(codename=codename, content_type=adverse_effect_ct)
                professional_permissions.append(perm)
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Permiso {codename} no encontrado'))
        
        # Intentar obtener permisos personalizados
        for codename in ['view_all_reports', 'manage_reports', 'receive_alerts']:
            try:
                perm = Permission.objects.get(codename=codename, content_type=adverse_effect_ct)
                professional_permissions.append(perm)
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Permiso personalizado {codename} no encontrado'))
        
        # Permisos para pacientes
        patient_permissions = []
        
        # Intentar obtener permisos para Medication
        for codename in ['add_medicamento', 'change_medicamento', 'delete_medicamento', 'view_medicamento']:
            try:
                perm = Permission.objects.get(codename=codename, content_type=medication_ct)
                patient_permissions.append(perm)
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Permiso {codename} no encontrado'))
        
        # Intentar obtener permisos para AdverseEffect (limitados)
        for codename in ['add_adverseeffect', 'view_adverseeffect']:
            try:
                perm = Permission.objects.get(codename=codename, content_type=adverse_effect_ct)
                patient_permissions.append(perm)
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Permiso {codename} no encontrado'))
        
        # Asignar permisos a grupos
        if professional_permissions:
            health_professionals.permissions.set(professional_permissions)
            self.stdout.write(self.style.SUCCESS(f'Asignados {len(professional_permissions)} permisos a profesionales'))
        
        if patient_permissions:
            patients.permissions.set(patient_permissions)
            self.stdout.write(self.style.SUCCESS(f'Asignados {len(patient_permissions)} permisos a pacientes'))
