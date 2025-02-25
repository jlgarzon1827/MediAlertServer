MediAlert API Documentation

Base URL: http://localhost:8000/api/

Authentication:
- JWT (JSON Web Token) authentication

User Management:
1. Register
   - POST /register/
     Create a new user account
     Body: {
       "username": "your_username", 
       "email": "your_email@example.com", 
       "password": "your_password",
       "is_professional": false,           // Optional, default: false
       "professional_id": "",              // Optional, for professionals
       "specialty": "",                    // Optional, for professionals
       "institution": ""                   // Optional, for professionals
     }

2. Login
   - POST /login/
     Authenticate user and obtain tokens
     Body: {"username": "your_username", "password": "your_password"}
     Response: {"access": "access_token", "refresh": "refresh_token"}

3. Refresh Token
   - POST /token/refresh/
     Obtain a new access token
     Body: {"refresh": "your_refresh_token"}

4. User Profile
   - GET /users/me/
     Retrieve current user profile information
     
   - PUT /users/update_profile/
     Update user profile information
     Body: {
       "first_name": "First Name",
       "last_name": "Last Name",
       "email": "email@example.com",
       "profile": {
         "phone": "123456789",
         "specialty": "Specialty",         // For professionals
         "institution": "Institution"      // For professionals
       }
     }

Token Usage:
- Use token in header: Authorization: Bearer <your_access_token>

Token Expiration:
- Access token: 30 minutes
- Refresh token: 1 day

Endpoints:

1. Medicamentos
   - GET /medicamentos/
     Retrieve list of medications for authenticated user
   - POST /medicamentos/
     Create a new medication
     Body: {"nombre": "Med Name", "dosis": "Dose", "frecuencia": "Frequency"}
   - GET /medicamentos/{id}/
     Retrieve specific medication details
   - PUT /medicamentos/{id}/
     Update medication details
   - DELETE /medicamentos/{id}/
     Delete a medication

2. Recordatorios
   - GET /recordatorios/
     Retrieve list of reminders for authenticated user
   - POST /recordatorios/
     Create a new reminder
     Body: {
       "medicamento": <medicamento_id>,
       "dosis": "Dose",
       "frecuencia": "DAILY|WEEKLY|MONTHLY|CUSTOM",
       "hora": "HH:MM:SS",
       "dias_semana": "1,2,3,4,5,6,7",     // Optional, for weekly frequency (1=Monday, 7=Sunday)
       "fecha_fin": "YYYY-MM-DD",          // Optional
       "activo": true,
       "notas": "Notes",                   // Optional
       "notificacion_previa": 15,          // Minutes before to notify, default: 0
       "sonido": "default",                // Optional
       "vibracion": true                   // Optional
     }
   - GET /recordatorios/{id}/
     Retrieve specific reminder details
   - PUT /recordatorios/{id}/
     Update reminder details
   - DELETE /recordatorios/{id}/
     Delete a reminder
   - POST /recordatorios/{id}/toggle_active/
     Toggle the active status of a reminder
   - GET /recordatorios/today/
     Get reminders scheduled for today
   - GET /recordatorios/upcoming/
     Get reminders scheduled for the next 24 hours

3. Registros de Toma
   - GET /registros-toma/
     Retrieve list of intake records for authenticated user
   - POST /registros-toma/
     Create a new intake record
     Body: {"recordatorio": <recordatorio_id>, "estado": "TOMADO|OMITIDO|POSPUESTO", "notas": "Notes"}
   - GET /registros-toma/{id}/
     Retrieve specific intake record details
   - PUT /registros-toma/{id}/
     Update intake record details
   - DELETE /registros-toma/{id}/
     Delete an intake record
   - POST /registros-toma/{id}/tomar/
     Mark medication as taken
   - POST /registros-toma/{id}/posponer/
     Postpone a reminder
     Body: {"minutos": 15}                 // Minutes to postpone
   - GET /registros-toma/by_date_range/
     Get intake records by date range
     Query Parameters:
       - start_date: Start date (YYYY-MM-DD)
       - end_date: End date (YYYY-MM-DD)
   - GET /registros-toma/statistics/
     Get intake statistics
     Query Parameters:
       - days: Number of days to analyze (default: 30)

4. Dispositivos
   - GET /dispositivos/
     Retrieve list of user devices
   - POST /dispositivos/
     Register a new device
     Body: {
       "token": "fcm_token",
       "nombre_dispositivo": "Device Name",
       "modelo": "Device Model",
       "sistema_operativo": "Android",
       "version_app": "1.0.0"
     }
   - DELETE /dispositivos/{id}/
     Delete a device
   - POST /dispositivos/register_token/
     Simplified endpoint to register FCM token
     Body: {"token": "fcm_token", "device_name": "Device Name"}
   - POST /dispositivos/test_notification/
     Send a test notification
     Body: {"token": "fcm_token"}

5. Farmacovigilancia
   - GET /adverse-effects/
     Retrieve list of adverse effects
     Note: Regular users see only their own reports, professionals see all reports
     Query Parameters:
       - severity: Filter by severity (LEVE, MODERADA, GRAVE, MORTAL)
       - type: Filter by type (A, B)
       - from: Start date (YYYY-MM-DD)
       - to: End date (YYYY-MM-DD)

   - POST /adverse-effects/
     Report new adverse effect
     Body: {
       "medication": <medication_id>,
       "description": "Effect description",
       "start_date": "YYYY-MM-DD",
       "end_date": "YYYY-MM-DD",
       "severity": "LEVE|MODERADA|GRAVE|MORTAL",
       "type": "A|B",
       "administration_route": "route",
       "dosage": "dosage",
       "frequency": "frequency"
     }

   - GET /adverse-effects/{id}/
     Retrieve specific adverse effect details

   - PUT /adverse-effects/{id}/
     Update adverse effect details

   - POST /adverse-effects/{id}/mark-as-reviewed/
     Mark adverse effect as reviewed
     Note: Requires professional access

6. Notifications
   - GET /notifications/
     Retrieve list of notifications for authenticated user
     
   - POST /notifications/{id}/mark-as-read/
     Mark notification as read
     
   - GET /notifications/unread/
     Retrieve unread notifications

7. Dashboard (Professional Access Required)
   - GET /dashboard/statistics/
     Get general statistics of adverse effects
     Response: {
       "total_reports": number,
       "by_severity": [{severity: string, count: number}],
       "by_type": [{type: string, count: number}]
     }

   - GET /dashboard/medication-statistics/
     Get statistics grouped by medication
     Response: {
       "most_reported": [{medication: string, count: number}],
       "by_severity": [{medication: string, severity: string, count: number}]
     }

   - GET /dashboard/trends/
     Get temporal analysis of adverse effects
     Response: {
       "daily_reports": [{date: string, count: number}],
       "severity_trend": [{severity: string, count: number}]
     }

   - GET /dashboard/pending-reviews/
     Get pending reviews information
     Response: {
       "pending": number,
       "urgent_pending": number,
       "recent_pending": [AdverseEffect]
     }

   - GET /dashboard/filtered-reports/
     Get filtered adverse effects reports
     Query Parameters:
       - severity: Filter by severity
       - medication: Filter by medication name
       - from: Start date (YYYY-MM-DD)
       - to: End date (YYYY-MM-DD)
     Response: {
       "count": number,
       "results": [AdverseEffect]
     }

   - GET /dashboard/export-csv/
     Export adverse effects data as CSV
     Query Parameters: [Same as filtered-reports]

   - GET /dashboard/export-json/
     Export adverse effects data as JSON
     Query Parameters: [Same as filtered-reports]

Data Structures:

1. AdverseEffect:
   {
     "id": number,
     "patient": number,
     "medication": number,
     "description": string,
     "start_date": string,
     "end_date": string,
     "severity": string,
     "type": string,
     "administration_route": string,
     "dosage": string,
     "frequency": string,
     "reported_at": string,
     "status": string
   }

2. UserProfile:
   {
     "user_type": "PATIENT|PROFESSIONAL",
     "professional_id": string,
     "specialty": string,
     "institution": string,
     "phone": string
   }

3. Recordatorio:
   {
     "id": number,
     "usuario": number,
     "medicamento": number,
     "medicamento_nombre": string,
     "dosis": string,
     "frecuencia": string,
     "hora": string,
     "dias_semana": string,
     "fecha_inicio": string,
     "fecha_fin": string,
     "activo": boolean,
     "notas": string,
     "notificacion_previa": number,
     "sonido": string,
     "vibracion": boolean,
     "created_at": string,
     "updated_at": string
   }

4. RegistroToma:
   {
     "id": number,
     "recordatorio": number,
     "medicamento_nombre": string,
     "fecha_programada": string,
     "fecha_toma": string,
     "estado": string,
     "notas": string,
     "created_at": string
   }

5. DispositivoUsuario:
   {
     "id": number,
     "token": string,
     "nombre_dispositivo": string,
     "modelo": string,
     "sistema_operativo": string,
     "version_app": string,
     "ultimo_acceso": string,
     "activo": boolean
   }

6. AlertNotification:
   {
     "id": number,
     "adverse_effect": number,
     "title": string,
     "message": string,
     "priority": "LOW|MEDIUM|HIGH|URGENT",
     "created_at": string,
     "read_at": string
   }

Roles and Permissions:
- All new users are assigned the "Patients" role by default
- Users can be registered as professionals with the is_professional flag
- Patients can only view and manage their own data
- Professionals can access dashboard endpoints and view all adverse effect reports
- Only professionals can mark reports as reviewed

Note: All endpoints (except register and login) require authentication. Include the access token in the request header.
