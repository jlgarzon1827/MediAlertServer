from rest_framework import serializers
from django.contrib.auth.models import User
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
