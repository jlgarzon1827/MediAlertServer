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

Note: All endpoints (except register and login) require authentication. Ensure to include the access token in the request header.
