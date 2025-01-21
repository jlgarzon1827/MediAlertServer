from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from .views import RegisterView, ProfileView, RecordatorioViewSet

router = DefaultRouter()
router.register(r'recordatorios', RecordatorioViewSet, basename='recordatorio')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('profile/', ProfileView.as_view(), name='auth_profile'),
    path('medicamentos/', views.MedicamentoListCreateView.as_view(), name='medicamento-list-create'),
    path('registros/', views.RegistroTomaListCreateView.as_view(), name='registrotoma-list-create'),
]
