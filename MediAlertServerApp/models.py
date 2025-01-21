from django.db import models
from django.contrib.auth.models import User

class Medicamento(models.Model):
    nombre = models.CharField(max_length=100)
    dosis = models.CharField(max_length=50)
    frecuencia = models.CharField(max_length=50)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre

class Recordatorio(models.Model):
    medicamento = models.ForeignKey(Medicamento, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField()
    completado = models.BooleanField(default=False)

    def __str__(self):
        return f"Recordatorio para {self.medicamento.nombre} a las {self.fecha_hora}"

class RegistroToma(models.Model):
    medicamento = models.ForeignKey(Medicamento, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    tomado = models.BooleanField(default=True)

    def __str__(self):
        return f"Toma de {self.medicamento.nombre} el {self.fecha_hora}"
