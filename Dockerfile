# Usar una imagen base ligera de Python compatible con ARM64 (para Raspberry Pi)
FROM python:3.13-slim

# Establecer variables de entorno para optimizar Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_ALLOWED_HOSTS="med-vigilance"

# Instalar herramientas del sistema y dependencias necesarias
RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    && apt-get clean

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /MedialertServer

# Copiar el archivo de dependencias
COPY requirements.txt /MedialertServer/

# Instalar las dependencias necesarias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente al contenedor
COPY . /MedialertServer/

# Hacer ejecutable el script de inicialización
RUN chmod +x /MedialertServer/entrypoint.sh

# Exponer el puerto en el que correrá Django (8000 por defecto)
EXPOSE 8000

# Usar el script como punto de entrada para inicializar y lanzar el servidor
CMD ["/MedialertServer/entrypoint.sh", "python", "manage.py", "runserver", "0.0.0.0:8000"]