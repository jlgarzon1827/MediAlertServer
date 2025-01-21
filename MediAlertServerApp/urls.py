from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from .views import CustomAuthToken, RegisterView, ProfileView

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('profile/', ProfileView.as_view(), name='auth_profile'),
    path('medicamentos/', views.MedicamentoListCreateView.as_view(), name='medicamento-list-create'),
    path('recordatorios/', views.RecordatorioListCreateView.as_view(), name='recordatorio-list-create'),
    path('registros/', views.RegistroTomaListCreateView.as_view(), name='registrotoma-list-create'),
]
