from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import UserProfile, Medicamento, Recordatorio, RegistroToma, AdverseEffect, AlertNotification

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['user_type', 'professional_id', 'specialty', 'institution', 'phone']
        
class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']
        read_only_fields = ['id']
        
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        
        # Actualizar campos del usuario
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Actualizar campos del perfil
        if profile_data:
            for attr, value in profile_data.items():
                setattr(instance.profile, attr, value)
            instance.profile.save()
            
        return instance
    
class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    is_professional = serializers.BooleanField(required=False, default=False)
    professional_id = serializers.CharField(required=False, allow_blank=True)
    specialty = serializers.CharField(required=False, allow_blank=True)
    institution = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'is_professional', 
                  'professional_id', 'specialty', 'institution')
    
    def create(self, validated_data):
        is_professional = validated_data.pop('is_professional', False)
        professional_id = validated_data.pop('professional_id', '')
        specialty = validated_data.pop('specialty', '')
        institution = validated_data.pop('institution', '')
        
        user = User.objects.create_user(**validated_data)
        
        # Actualizar perfil si es profesional
        if is_professional:
            user.profile.user_type = 'PROFESSIONAL'
            user.profile.professional_id = professional_id
            user.profile.specialty = specialty
            user.profile.institution = institution
            user.profile.save()
        
        return user

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
