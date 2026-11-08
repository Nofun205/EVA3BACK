#!/usr/bin/env bash
# ==============================================================================
# BUILDCORP - SCRIPT DE DESPLIEGUE AUTOMÁTICO EN AWS EC2 (UBUNTU 22.04 / 24.04 LTS)
# ==============================================================================
# Evaluación Parcial N°3: Desarrollo Backend - Inacap
# ==============================================================================

set -e

echo "============================================================"
echo "    INICIANDO DESPLIEGUE DE BUILDCORP EN AWS EC2            "
echo "============================================================"

# 1. Actualización de paquetes del sistema
echo "==> [1/7] Actualizando repositorios y paquetes del sistema..."
sudo apt update && sudo apt upgrade -y

# 2. Instalación de dependencias (Python, PostgreSQL, Nginx, Git, Libpq)
echo "==> [2/7] Instalando Python 3, PostgreSQL, Nginx y dependencias..."
sudo apt install -y python3 python3-pip python3-venv \
    postgresql postgresql-contrib libpq-dev \
    nginx git curl

# 3. Configuración de PostgreSQL
echo "==> [3/7] Configurando servidor de base de datos PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Crear base de datos y usuario de PostgreSQL si no existen
sudo -u postgres psql -c "CREATE DATABASE buildcorp_db;" || true
sudo -u postgres psql -c "CREATE USER buildcorp_user WITH PASSWORD 'buildcorp_pass_2026';" || true
sudo -u postgres psql -c "ALTER ROLE buildcorp_user SET client_encoding TO 'utf8';" || true
sudo -u postgres psql -c "ALTER ROLE buildcorp_user SET default_transaction_isolation TO 'read committed';" || true
sudo -u postgres psql -c "ALTER ROLE buildcorp_user SET timezone TO 'America/Santiago';" || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE buildcorp_db TO buildcorp_user;" || true
sudo -u postgres psql -d buildcorp_db -c "GRANT ALL ON SCHEMA public TO buildcorp_user;" || true

# 4. Configurar Entorno Virtual de Python y Dependencias
echo "==> [4/7] Configurando entorno virtual e instalando paquetes Python..."
cd /home/ubuntu/EVA3BACK || cd "$(pwd)"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. Configuración de variables de entorno de producción
echo "==> [5/7] Configurando archivo .env para PostgreSQL en EC2..."
cat << 'EOF' > .env
DEBUG=False
SECRET_KEY=django-insecure-buildcorp-secret-key-evaluacion-3-inacap-2026
ALLOWED_HOSTS=*

# Conexión directa a PostgreSQL
DATABASE_URL=postgresql://buildcorp_user:buildcorp_pass_2026@localhost:5432/buildcorp_db
DB_ENGINE=postgresql
DB_NAME=buildcorp_db
DB_USER=buildcorp_user
DB_PASSWORD=buildcorp_pass_2026
DB_HOST=localhost
DB_PORT=5432
USE_SQLITE_FALLBACK=False

CORS_ALLOW_ALL_ORIGINS=True
EOF

# 6. Migraciones, estáticos y datos de prueba
echo "==> [6/7] Aplicando migraciones de ORM y recopilando estáticos..."
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_data

# Asegurar permisos en carpetas media y staticfiles
sudo chown -R ubuntu:www-data media staticfiles
sudo chmod -R 775 media staticfiles

# 7. Configuración de Gunicorn y Nginx
echo "==> [7/7] Configurando servicios de producción (Gunicorn + Nginx)..."

# Instalar y habilitar servicio Systemd para Gunicorn
sudo cp deploy/buildcorp.service /etc/systemd/system/buildcorp.service
sudo systemctl daemon-reload
sudo systemctl start buildcorp
sudo systemctl enable buildcorp

# Configurar Nginx
sudo cp deploy/nginx_buildcorp.conf /etc/nginx/sites-available/buildcorp
sudo ln -sf /etc/nginx/sites-available/buildcorp /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

# Obtener IP Pública de EC2
PUBLIC_IP=$(curl -s http://checkip.amazonaws.com || curl -s ifconfig.me || echo "<TU_IP_PUBLICA_EC2>")

echo "============================================================"
echo "    ✔ DESPLIEGUE EN AWS EC2 COMPLETADO EXITOSAMENTE        "
echo "============================================================"
echo "Accede a la plataforma web pública en:"
echo "http://${PUBLIC_IP}/"
echo ""
echo "Panel Django Admin en:"
echo "http://${PUBLIC_IP}/admin/"
echo "Credenciales: admin / Admin123!"
echo "============================================================"
