#!/bin/bash

set -e

if [ -d "./db.sqlite3" ]; then
  echo "⚠️  Error: db.sqlite3 es un directorio. Eliminándolo..."
  rm -rf ./db.sqlite3
fi

if [ ! -f "./db.sqlite3" ]; then
  echo "🔧 Creando archivo SQLite..."
  touch ./db.sqlite3
  chmod 666 ./db.sqlite3
fi

echo "✅ Base de datos lista. Aplicando migraciones..."
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
