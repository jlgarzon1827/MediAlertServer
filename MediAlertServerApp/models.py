from django.db import models
from django.conf import settings

class Medicamento(models.Model):
    nombre = models.CharField(max_length=100)
    dosis = models.CharField(max_length=50)
    frecuencia = models.CharField(max_length=50)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombrez

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
