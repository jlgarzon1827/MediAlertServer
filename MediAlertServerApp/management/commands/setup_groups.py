from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from MediAlertServerApp.models import AdverseEffect, Medicamento

class Command(BaseCommand):
    help = 'Configura los grupos y permisos iniciales'

    def handle(self, *args, **options):
        # Crear grupo para admins
        admins, created = Group.objects.get_or_create(name='Admins')
        if created:
            self.stdout.write(self.style.SUCCESS('Grupo "Admins" creado'))

        # Crear grupo para supervisores
        supervisors, created = Group.objects.get_or_create(name='Supervisors')
        if created:
            self.stdout.write(self.style.SUCCESS('Grupo "Supervisors" creado'))

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
        
        # Crear permiso personalizado para asignar revisores
        assign_reviewer_permission, created = Permission.objects.get_or_create(
            codename='can_assign_reviewers',
            name='Can assign reviewers to adverse effects',
            content_type=adverse_effect_ct
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Permiso "can_assign_reviewers" creado'))


        # Permisos para profesionales
        admin_permissions = []
        supervisor_permissions = []
        professional_permissions = []
        
        # Intentar obtener permisos para AdverseEffect
        for codename in ['view_adverseeffect', 'change_adverseeffect']:
            try:
                perm = Permission.objects.get(codename=codename, content_type=adverse_effect_ct)
                professional_permissions.append(perm)
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Permiso {codename} no encontrado'))

        # Intentar obtener permisos personalizados
        for codename in ['view_all_reports', 'manage_reports', 'receive_alerts', 'can_assign_reviewers']:
            try:
                perm = Permission.objects.get(codename=codename, content_type=adverse_effect_ct)
                admin_permissions.append(perm)
                supervisor_permissions.append(perm)
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

        # Asignar permisos a grupos
        if admin_permissions:
            admins.permissions.set(admin_permissions)
            self.stdout.write(self.style.SUCCESS(f'Asignados {len(admin_permissions)} permisos a admins'))
            
        if supervisor_permissions:
            supervisors.permissions.set(supervisor_permissions)
            self.stdout.write(self.style.SUCCESS(f'Asignados {len(supervisor_permissions)} permisos a supervisores'))

        # Asignar al usuario jesyl como administrador
        try:
            admin_user = User.objects.get(username='jesyl')  # Cambiar el nombre de usuario si es necesario
            admin_user.profile.user_type = 'ADMIN'
            admin_user.profile.save()
            
            # Añadir al grupo de administradores
            admins.user_set.add(admin_user)

            # Asignar todos los permisos del grupo Admins directamente al usuario
            for perm in admin_permissions:
                admin_user.user_permissions.add(perm)

            self.stdout.write(self.style.SUCCESS('Usuario "jesyl" configurado como administrador con todos los permisos.'))
        
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Usuario "jesyl" no encontrado. Por favor, crea el usuario antes de ejecutar este script.'))
