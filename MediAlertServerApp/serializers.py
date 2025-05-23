from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, MedicamentoMaestro, Medicamento, Recordatorio, \
    RegistroToma, AdverseEffect, AlertNotification, DispositivoUsuario, Institution

class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ['id', 'name', 'address', 'contact_email', 'phone_number']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['user_type', 'data_protection_accepted', 'data_protection_accepted_at', 'professional_id', 'specialty', 'institution', 'phone']
        
class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']
        read_only_fields = ['id']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user_type'] = instance.profile.user_type
        return data
        
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
    
class CombinedProfileSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']

    def get_profile(self, obj):
        try:
            profile = UserProfile.objects.get(user=obj)
            return {
                'user_type': profile.user_type,
                'data_protection_accepted': profile.data_protection_accepted,
                'professional_id': profile.professional_id,
                'specialty': profile.specialty,
                'institution': profile.institution.id if profile.institution else None,
                'phone': profile.phone,
            }
        except UserProfile.DoesNotExist:
            return None
    
class DispositivoUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispositivoUsuario
        fields = ('id', 'token', 'nombre_dispositivo', 'modelo', 'sistema_operativo', 'version_app', 'ultimo_acceso', 'activo')
        read_only_fields = ('id', 'ultimo_acceso')

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    is_professional = serializers.BooleanField(required=False, default=False)
    professional_id = serializers.CharField(required=False, allow_blank=True)
    specialty = serializers.CharField(required=False, allow_blank=True)
    institution = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.all(), required=False, allow_null=True
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'is_professional', 
                  'professional_id', 'specialty', 'institution')
    
    def create(self, validated_data):
        is_professional = validated_data.pop('is_professional', False)
        professional_id = validated_data.pop('professional_id', '')
        specialty = validated_data.pop('specialty', '')
        institution = validated_data.pop('institution', None)
        
        user = User.objects.create_user(**validated_data)
        
        if is_professional:
            user.profile.user_type = 'PROFESSIONAL'
            user.profile.professional_id = professional_id
            user.profile.specialty = specialty
            user.profile.institution = institution
        else:
            default_institution = Institution.objects.first()
            user.profile.user_type = 'PATIENT'
            user.profile.institution = default_institution

        user.profile.save()
        
        return user

class MedicamentoMaestroSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicamentoMaestro
        fields = ['id', 'nombre', 'dosis', 'forma_farmaceutica', 'principio_activo', 'concentracion', 'via_administracion', 'frecuencia']

class MedicamentoSerializer(serializers.ModelSerializer):
    medicamento_maestro_id = serializers.PrimaryKeyRelatedField(
        source='medicamento_maestro',
        queryset=MedicamentoMaestro.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Medicamento
        fields = ['id', 'medicamento_maestro_id', 'dosis_personalizada', 'frecuencia_personalizada', 'usuario']
        read_only_fields = ['usuario']

class RecordatorioSerializer(serializers.ModelSerializer):
    medicamento_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Recordatorio
        fields = '__all__'
        read_only_fields = ('usuario', 'created_at', 'updated_at')
    
    def get_medicamento_nombre(self, obj):
        return obj.medicamento.medicamento_maestro.nombre if obj.medicamento else None
    
    def validate(self, data):
        # Validar que fecha_fin es posterior a fecha_inicio si existe
        if 'fecha_fin' in data and data['fecha_fin'] and data['fecha_fin'] < data.get('fecha_inicio', self.instance.fecha_inicio if self.instance else None):
            raise serializers.ValidationError("La fecha de fin debe ser posterior a la fecha de inicio")
        return data

class RegistroTomaSerializer(serializers.ModelSerializer):
    medicamento_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = RegistroToma
        fields = '__all__'
        read_only_fields = ('created_at',)
    
    def get_medicamento_nombre(self, obj):
        return obj.recordatorio.medicamento.medicamento_maestro.nombre if obj.recordatorio and obj.medicamento.medicamento_maestro.nombre else None
    
class AdverseEffectSerializer(serializers.ModelSerializer):
    medicamento_nombre = serializers.CharField(source='medication.nombre', read_only=True)
    additional_info = serializers.CharField(required=False, allow_null=True)
    reclamation_reason = serializers.CharField(required=False, allow_null=True)
    revertion_reason = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = AdverseEffect
        fields = '__all__'

    class Meta:
        model = AdverseEffect
        fields = '__all__'
        read_only_fields = ('reported_at', 'updated_at', 'status', 'medicamento_nombre')

    def validate(self, data):
        if 'end_date' in data and data['end_date'] < data['start_date']:
            raise serializers.ValidationError("La fecha de fin debe ser posterior a la fecha de inicio")
        return data


class AlertNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertNotification
        fields = '__all__'
        read_only_fields = ('created_at', 'read_at')
