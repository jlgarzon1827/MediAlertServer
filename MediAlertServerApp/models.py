from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    USER_TYPES = [
        ('PATIENT', 'Paciente'),
        ('PROFESSIONAL', 'Profesional de la salud')
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='PATIENT')
    professional_id = models.CharField(max_length=50, blank=True, null=True)
    specialty = models.CharField(max_length=100, blank=True, null=True)
    institution = models.CharField(max_length=200, blank=True, null=True)
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

class Medicamento(models.Model):
    nombre = models.CharField(max_length=100)
    dosis = models.CharField(max_length=50)
    frecuencia = models.CharField(max_length=50)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre

class Recordatorio(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    medicamento = models.CharField(max_length=100, null=True, blank=True)
    dosis = models.CharField(max_length=50, null=True, blank=True)
    frecuencia = models.CharField(max_length=50, null=True, blank=True)
    hora = models.TimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.medicamento} - {self.hora}"

class RegistroToma(models.Model):
    medicamento = models.ForeignKey(Medicamento, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    tomado = models.BooleanField(default=True)

    def __str__(self):
        return f"Toma de {self.medicamento.nombre} el {self.fecha_hora}"

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
    status = models.CharField(max_length=20, default='PENDING')

    class Meta:
        ordering = ['-reported_at']
        permissions = [
            ("view_all_reports", "Can view all adverse effect reports"),
            ("manage_reports", "Can manage adverse effect reports"),
            ("receive_alerts", "Can receive adverse effect alerts")
        ]

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
