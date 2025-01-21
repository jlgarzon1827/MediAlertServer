from django.urls import path
from . import views

urlpatterns = [
    path('medicamentos/', views.MedicamentoListCreateView.as_view(), name='medicamento-list-create'),
    path('recordatorios/', views.RecordatorioListCreateView.as_view(), name='recordatorio-list-create'),
    path('registros/', views.RegistroTomaListCreateView.as_view(), name='registrotoma-list-create'),
]

