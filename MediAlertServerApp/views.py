from rest_framework import generics, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Medicamento, Recordatorio, RegistroToma
from .serializers import MedicamentoSerializer, RecordatorioSerializer, RegistroTomaSerializer, UserSerializer, UserProfileSerializer
from django.contrib.auth.models import User

class MedicamentoListCreateView(generics.ListCreateAPIView):
    queryset = Medicamento.objects.all()
    serializer_class = MedicamentoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

class RecordatorioListCreateView(generics.ListCreateAPIView):
    queryset = Recordatorio.objects.all()
    serializer_class = RecordatorioSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

class RegistroTomaListCreateView(generics.ListCreateAPIView):
    queryset = RegistroToma.objects.all()
    serializer_class = RegistroTomaSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email
        })

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UserSerializer(user).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        })

class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user
