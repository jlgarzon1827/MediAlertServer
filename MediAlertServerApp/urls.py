from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from .views import RegisterView, ProfileView, MedicamentoViewSet, RecordatorioViewSet, RegistroTomaViewSet, AdverseEffectViewSet, AlertNotificationViewSet, DashboardViewSet

router = DefaultRouter()
router.register(r'medicamentos', MedicamentoViewSet, basename='medicamento')
router.register(r'recordatorios', RecordatorioViewSet, basename='recordatorio')
router.register(r'registros-toma', RegistroTomaViewSet, basename='registrotoma')
router.register(r'adverse-effects', AdverseEffectViewSet, basename='adverse-effect')
router.register(r'notifications', AlertNotificationViewSet, basename='notification')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('profile/', ProfileView.as_view(), name='auth_profile'),
]
