#!/bin/bash

# Salir inmediatamente si algún comando falla
set -e

echo "Aplicando migraciones..."
python manage.py makemigrations
python manage.py migrate

echo "Creando superusuario..."
echo "from django.contrib.auth.models import User; User.objects.create_superuser('jesyl', 'admin@example.com', 'jesylpassword') if not User.objects.filter(username='jesyl').exists() else print('Superusuario ya existe')" | python manage.py shell

echo "Configurando grupos y permisos..."
python manage.py setup_groups

echo "Cargando datos iniciales..."
python manage.py loaddata medicamentos_maestros

echo "Iniciando servidor Django..."
exec "$@"
