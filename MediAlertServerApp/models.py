from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import assign_reviewer_to_report

class Institution(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.TextField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    USER_TYPES = [
        ('PATIENT', 'Paciente'),
        ('PROFESSIONAL', 'Profesional de la salud'),
        ('ADMIN', 'Admin'),
        ('SUPERVISOR', 'Supervisor')
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='PATIENT')
    professional_id = models.CharField(max_length=50, blank=True, null=True)
    specialty = models.CharField(max_length=100, blank=True, null=True)
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crear perfil automáticamente cuando se crea un usuario"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Guardar perfil cuando se guarda el usuario"""
    instance.profile.save()

class DispositivoUsuario(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dispositivos')
    token = models.CharField(max_length=255, unique=True)
    nombre_dispositivo = models.CharField(max_length=100, blank=True, null=True)
    modelo = models.CharField(max_length=100, blank=True, null=True)
    sistema_operativo = models.CharField(max_length=50, blank=True, null=True)
    version_app = models.CharField(max_length=20, blank=True, null=True)
    ultimo_acceso = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.usuario.username} - {self.nombre_dispositivo or 'Dispositivo'}"
    
    class Meta:
        unique_together = ('usuario', 'token')

class MedicamentoMaestro(models.Model):
    nombre = models.CharField(max_length=100)
    dosis = models.CharField(max_length=50)
    forma_farmaceutica = models.CharField(max_length=50, blank=True)
    principio_activo = models.CharField(max_length=100, blank=True)
    concentracion = models.CharField(max_length=50, blank=True)
    via_administracion = models.CharField(max_length=50, blank=True)
    frecuencia = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.nombre

class Medicamento(models.Model):
    medicamento_maestro = models.ForeignKey(MedicamentoMaestro, on_delete=models.CASCADE)
    dosis_personalizada = models.CharField(max_length=50, blank=True)
    frecuencia_personalizada = models.CharField(max_length=50, blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.medicamento_maestro.nombre} - {self.usuario.username}"

class Recordatorio(models.Model):
    FREQUENCY_CHOICES = [
        ('DAILY', 'Diario'),
        ('WEEKLY', 'Semanal'),
        ('MONTHLY', 'Mensual'),
        ('CUSTOM', 'Personalizado')
    ]
    
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recordatorios')
    medicamento = models.ForeignKey('Medicamento', on_delete=models.CASCADE, related_name='recordatorios')
    dosis = models.CharField(max_length=50)
    frecuencia = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='DAILY')
    hora = models.TimeField()
    dias_semana = models.CharField(max_length=20, blank=True, null=True)  # Formato: "1,2,3,4,5,6,7" para días de la semana
    fecha_inicio = models.DateField(auto_now_add=True)
    fecha_fin = models.DateField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    notas = models.TextField(blank=True, null=True)
    
    # Campos para notificaciones
    notificacion_previa = models.IntegerField(default=0)  # Minutos antes para notificar
    sonido = models.CharField(max_length=50, default='default')
    vibracion = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.medicamento.medicamento_maestro.nombre} - {self.hora}"
    
    class Meta:
        ordering = ['hora']

class RegistroToma(models.Model):
    STATUS_CHOICES = [
        ('TOMADO', 'Tomado'),
        ('OMITIDO', 'Omitido'),
        ('POSPUESTO', 'Pospuesto')
    ]
    
    recordatorio = models.ForeignKey(Recordatorio, on_delete=models.CASCADE, related_name='registros')
    fecha_programada = models.DateTimeField()
    fecha_toma = models.DateTimeField(blank=True, null=True)
    estado = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OMITIDO')
    notas = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.recordatorio} - {self.fecha_programada.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-fecha_programada']

class AdverseEffect(models.Model):
    SEVERITY_CHOICES = [
        ('LEVE', 'Leve'),
        ('MODERADA', 'Moderada'),
        ('GRAVE', 'Grave'),
        ('MORTAL', 'Mortal')
    ]

    TYPE_CHOICES = [
        ('A', 'Tipo A - Aumentado/Predecible'),
        ('B', 'Tipo B - Bizarro/No predecible')
    ]

    STATUS_CHOICES = [
        ('CREATED', 'Created'),
        ('ASSIGNED', 'Assigned'),
        ('IN_REVISION', 'En Revisión'),
        ('PENDING_INFORMATION', 'Pending information'),
        ('REJECTED', 'Rejected'),
        ('RECLAIMED', 'Reclaimed'),
        ('APPROVED', 'Approved')
    ]

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='adverse_effects')
    medication = models.ForeignKey('Medicamento', on_delete=models.CASCADE)
    
    # Detalles del efecto adverso
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    
    # Detalles de la administración
    administration_route = models.CharField(max_length=100)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    
    # Metadatos
    reported_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CREATED')

    reviewer = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_reviews')

    additional_info = models.TextField(null=True, blank=True)
    reclamation_reason = models.TextField(null=True, blank=True)
    revertion_reason = models.TextField(null=True, blank=True)

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-reported_at']
        permissions = [
            ("view_all_reports", "Can view all adverse effect reports"),
            ("manage_reports", "Can manage adverse effect reports"),
            ("receive_alerts", "Can receive adverse effect alerts")
        ]

    def save(self, *args, **kwargs):
        if not self.pk and self.status == 'CREATED':
            reviewer = assign_reviewer_to_report()
            if reviewer:
                self.reviewer = reviewer
                self.status = 'ASSIGNED'
        
        super().save(*args, **kwargs)

class AlertNotification(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Baja'),
        ('MEDIUM', 'Media'),
        ('HIGH', 'Alta'),
        ('URGENT', 'Urgente')
    ]

    adverse_effect = models.ForeignKey(AdverseEffect, on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
