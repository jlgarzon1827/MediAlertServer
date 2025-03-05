from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from .views import UserViewSet, DispositivoUsuarioViewSet, RegisterView, ProfileView, \
    MedicamentoViewSet, RecordatorioViewSet, RegistroTomaViewSet, AdverseEffectViewSet, \
    AlertNotificationViewSet, DashboardViewSet

router = DefaultRouter()
router.register(r'medicamentos', MedicamentoViewSet, basename='medicamento')
router.register(r'recordatorios', RecordatorioViewSet, basename='recordatorio')
router.register(r'registros-toma', RegistroTomaViewSet, basename='registro-toma')
router.register(r'adverse-effects', AdverseEffectViewSet, basename='adverse-effect')
router.register(r'notifications', AlertNotificationViewSet, basename='notification')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'users', UserViewSet, basename='user')
router.register(r'dispositivos', DispositivoUsuarioViewSet, basename='dispositivo')

urlpatterns = [
    path('', include(router.urls)),
    path('adverse-effects/<int:pk>/mark-as-reviewed/', views.AdverseEffectViewSet.as_view({'post': 'mark_as_reviewed'}), name='adverse-effect-mark-as-reviewed'),
    path('adverse-effects/<int:pk>/assign-reviewer/', views.AdverseEffectViewSet.as_view({'post': 'assign_reviewer'}), name='adverse-effect-assign-reviewer'),
    path('adverse-effects/filtered-reports/', AdverseEffectViewSet.as_view({'get': 'filtered_reports'}), name='adverse-effect-filtered-reports'),
    path('dashboard/pending-reviews/', DashboardViewSet.as_view({'get': 'pending_reviews'}), name='dashboard-pending-reviews'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('profile/', ProfileView.as_view(), name='auth_profile'),
]
