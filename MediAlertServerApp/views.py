from rest_framework import generics
from .models import Medicamento, Recordatorio, RegistroToma
from .serializers import MedicamentoSerializer, RecordatorioSerializer, RegistroTomaSerializer

class MedicamentoListCreateView(generics.ListCreateAPIView):
    queryset = Medicamento.objects.all()
    serializer_class = MedicamentoSerializer

class RecordatorioListCreateView(generics.ListCreateAPIView):
    queryset = Recordatorio.objects.all()
    serializer_class = RecordatorioSerializer

class RegistroTomaListCreateView(generics.ListCreateAPIView):
    queryset = RegistroToma.objects.all()
    serializer_class = RegistroTomaSerializer

