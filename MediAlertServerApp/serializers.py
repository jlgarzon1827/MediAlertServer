from rest_framework import serializers
from .models import Medicamento, Recordatorio, RegistroToma

class MedicamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicamento
        fields = ['id', 'nombre', 'dosis', 'frecuencia', 'usuario']

class RecordatorioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recordatorio
        fields = ['id', 'medicamento', 'fecha_hora', 'completado']

class RegistroTomaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroToma
        fields = ['id', 'medicamento', 'fecha_hora', 'tomado']
