from rest_framework import generics, permissions, viewsets
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

class RecordatorioViewSet(viewsets.ModelViewSet):
    serializer_class = RecordatorioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Recordatorio.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

class RegistroTomaListCreateView(generics.ListCreateAPIView):
    queryset = RegistroToma.objects.all()
    serializer_class = RegistroTomaSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

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
