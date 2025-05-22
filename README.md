MEDIALERT API - DOCUMENTACIÓN
======================================

URL BASE: http://localhost:8000/api/

AUTENTICACIÓN
-------------
- Sistema JWT (JSON Web Token)
- Incluir en cabeceras: Authorization: Bearer <access_token>
- Tokens:
  * Access: 30 minutos de validez
  * Refresh: 1 día de validez
- Endpoints de autenticación:
  POST /register/      Registrar nuevo usuario
  POST /login/         Obtener tokens
  POST /token/refresh/ Refrescar token de acceso

GESTIÓN DE USUARIOS
-------------------
ENDPOINTS PRINCIPALES:
- GET /users/me/              Obtener perfil actual
- PUT /users/update_profile/  Actualizar datos de usuario
- POST /users/{id}/set_role/  Cambiar rol de usuario (Admin)

REGISTRO DE USUARIO (POST /register/):
{
  "username": "nombre_usuario",
  "email": "email@valido.com",
  "password": "contraseña_segura",
  "is_professional": false,
  "professional_id": "OPCIONAL_PROFESIONALES",
  "specialty": "OPCIONAL_PROFESIONALES",
  "institution": 1
}

ACTUALIZACIÓN DE PERFIL (PUT /users/update_profile/):
{
  "first_name": "Nombre",
  "profile": {
    "phone": "+34 600 000 000",
    "specialty": "Especialidad (profesionales)",
    "institution": 2
  }
}

GESTIÓN DE INSTITUCIONES
------------------------
ENDPOINTS:
- GET /institutions/          Listar instituciones
- POST /institutions/         Crear nueva (Admin)
- PUT /institutions/{id}/     Actualizar (Admin/Supervisor)
- DELETE /institutions/{id}/  Eliminar (Admin)

ESTRUCTURA DE INSTITUCIÓN:
{
  "id": 1,
  "name": "Hospital General",
  "address": "Calle Principal 123",
  "phone": "555-1234",
  "code": "HOSP-001"
}

MEDICAMENTOS Y RECORDATORIOS
----------------------------
ENDPOINTS DE MEDICAMENTOS:
- GET/POST /medicamentos/      Listar/Crear medicamentos
- GET/PUT/DELETE /medicamentos/{id}/  Gestionar específico

ENDPOINTS DE RECORDATORIOS:
- POST /recordatorios/  Crear nuevo recordatorio
{
  "medicamento": 5,
  "hora": "08:00:00",
  "frecuencia": "DIARIA",
  "dias_semana": "1,3,5",
  "notificacion_previa": 15
}

- GET /recordatorios/today/    Recordatorios para hoy
- POST /recordatorios/{id}/toggle_active/  Activar/Desactivar

FARMACOVIGILANCIA
-----------------
ENDPOINTS PRINCIPALES:
- POST /adverse-effects/  Reportar efecto adverso
{
  "medication": 12,
  "description": "Descripción detallada",
  "severity": "GRAVE",
  "type": "B",
  "institution": 1
}

- GET /adverse-effects/filtered-reports/  Reportes filtrados
  Parámetros: severity, type, from, to, status, institution

- POST /adverse-effects/{id}/assign-reviewer/  Asignar revisor
{
  "reviewer_id": 45
}

FLUJO DE TRABAJO:
- POST /adverse-effects/{id}/start-review/     Iniciar revisión
- POST /adverse-effects/{id}/request-additional-info/ Solicitar info
- POST /adverse-effects/{id}/add-message/     Enviar mensaje al chat

DASHBOARD PROFESIONAL
---------------------
ENDPOINTS ESTADÍSTICOS:
- GET /dashboard/statistics/        Estadísticas generales
- GET /dashboard/medication-statistics/  Estadísticas por medicamento
- GET /dashboard/trends/            Tendencias temporales

EXPORTACIÓN DE DATOS:
- GET /dashboard/export-csv/    Exportar a CSV
- GET /dashboard/export-json/   Exportar a JSON
- GET /dashboard/generate_pdf_report/  Generar PDF

NOTIFICACIONES
--------------
ENDPOINTS:
- GET /notifications/          Listar todas
- GET /notifications/unread/   No leídas
- POST /notifications/{id}/mark-as-read/  Marcar como leída

ESTRUCTURA DE NOTIFICACIÓN:
ID | Título | Mensaje | Prioridad (BAJA/MEDIA/ALTA/URGENTE) | Fecha

ESTRUCTURAS DE DATOS
--------------------
USUARIO PROFESIONAL:
{
  "id": 45,
  "user_type": "PROFESSIONAL",
  "institution": {
    "id": 2,
    "name": "Clínica Privada"
  },
  "specialty": "Oncología"
}

REPORTE COMPLETO:
{
  "id": 123,
  "status": "EN_REVISION",
  "chat_messages": [
    {
      "sender": "patient",
      "message": "Síntomas desde las 10 AM",
      "timestamp": "2023-08-20T10:30:00Z"
    }
  ],
  "medication": {
    "id": 12,
    "nombre": "Ibuprofeno"
  }
}

ROLES Y PERMISOS
----------------
PACIENTE:
- Gestionar sus medicamentos y reportes
- Participar en chat de sus casos

PROFESIONAL:
- Acceso a dashboard analítico
- Revisar reportes asignados
- Solicitar información adicional

SUPERVISOR:
- Gestionar instituciones
- Asignar revisores
- Exportar datos institucionales

ADMIN:
- Administración completa del sistema
- Gestión de usuarios y roles
- Auditoría de todas las operaciones

CÓDIGOS DE ERROR
----------------
- 401: No autenticado
- 403: Acceso prohibido
- 404: Recurso no encontrado
- 429: Demasiadas solicitudes
- 500: Error interno del servidor

NOTAS IMPORTANTES
-----------------
1. Formatos de fecha: YYYY-MM-DD (ISO 8601)
2. Campos requeridos marcados en documentación
3. Límite de tasa: 100 peticiones/minuto
4. Todos los endpoints (excepto /register/ y /login/) requieren autenticación
5. Zona horaria: UTC