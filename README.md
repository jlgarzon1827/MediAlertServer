MediAlert API Documentation

Base URL: http://localhost:8000/api/

Authentication:
- JWT (JSON Web Token) authentication

User Management:
1. Register
   - POST /register/
     Create a new user account
     Body: {"username": "your_username", "email": "your_email@example.com", "password": "your_password"}

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
   - GET /profile/
     Retrieve user profile information

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
     Body: {"medicamento": "Med Name", "dosis": "Dose", "frecuencia": "Frequency", "hora": "HH:MM:SS", "activo": true}
   - GET /recordatorios/{id}/
     Retrieve specific reminder details
   - PUT /recordatorios/{id}/
     Update reminder details
   - DELETE /recordatorios/{id}/
     Delete a reminder

3. Registros de Toma
   - GET /registros-toma/
     Retrieve list of intake records for authenticated user
   - POST /registros-toma/
     Create a new intake record
     Body: {"medicamento": <medicamento_id>, "tomado": true}
   - GET /registros-toma/{id}/
     Retrieve specific intake record details
   - PUT /registros-toma/{id}/
     Update intake record details
   - DELETE /registros-toma/{id}/
     Delete an intake record

4. Farmacovigilancia
   - GET /adverse-effects/
     Retrieve list of adverse effects
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

5. Dashboard (Professional Access Required)
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

Permissions:
- Regular users can only view and report their own adverse effects
- Professional users can access dashboard endpoints and view all reports
- Only users with manage_reports permission can mark reports as reviewed

Note: All endpoints (except register and login) require authentication. Include the access token in the request header.
