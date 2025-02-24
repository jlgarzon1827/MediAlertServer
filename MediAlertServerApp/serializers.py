from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Medicamento, Recordatorio, RegistroToma, AdverseEffect, AlertNotification

class MedicamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicamento
        fields = ['id', 'nombre', 'dosis', 'frecuencia', 'usuario']
        read_only_fields = ['usuario']


class RecordatorioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recordatorio
        fields = ['id', 'medicamento', 'dosis', 'frecuencia', 'hora', 'activo']
        read_only_fields = ['id']


class RegistroTomaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroToma
        fields = ['id', 'medicamento', 'fecha_hora', 'tomado']

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

class AdverseEffectSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdverseEffect
        fields = '__all__'
        read_only_fields = ('reported_at', 'updated_at', 'status')

    def validate(self, data):
        # Validar que end_date es posterior a start_date si existe
        if 'end_date' in data and data['end_date'] < data['start_date']:
            raise serializers.ValidationError("La fecha de fin debe ser posterior a la fecha de inicio")
        return data

class AlertNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertNotification
        fields = '__all__'
        read_only_fields = ('created_at', 'read_at')
