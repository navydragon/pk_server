#!/usr/bin/env bash
set -e

###############################################################################
# setup_django_app.sh
#
# Тестовый скрипт стартовой установки Django backend + frontend
# на сервере Ubuntu/Debian без Docker.
#
# ВНИМАНИЕ:
# - Перед запуском обязательно отредактируй переменные в разделе "НАСТРОЙКИ".
# - Скрипт предполагает структуру:
#     ~/PROJECT_NAME/backend
#     ~/PROJECT_NAME/frontend
###############################################################################

##################################
# НАСТРОЙКИ (ОТРЕДАКТИРУЙ ПОД СЕБЯ)
##################################

# Имя проекта (используется в путях и именах сервисов)
PROJECT_NAME="myproject"

# Пользователь Linux, под которым будет запускаться gunicorn
LINUX_USER="nnd"

# Домен для nginx / certbot
DOMAIN="example.com"

# Пути проекта
APP_DIR="/home/${LINUX_USER}/${PROJECT_NAME}"
BACKEND_DIR="${APP_DIR}/backend"
FRONTEND_DIR="${APP_DIR}/frontend"

# Git-репозитории
BACKEND_REPO_URL="git@github.com:yourname/your-backend-repo.git"
FRONTEND_REPO_URL="git@github.com:yourname/your-frontend-repo.git"

# Настройки БД PostgreSQL
DB_NAME="${PROJECT_NAME}_db"
DB_USER="${PROJECT_NAME}_user"
DB_PASSWORD="change_me_strong_password"

# Django WSGI-модуль (например, config.wsgi:application)
DJANGO_WSGI_MODULE="config.wsgi:application"

# Директория, откуда nginx будет раздавать собранный фронтенд
NGINX_FRONT_ROOT="/var/www/${PROJECT_NAME}"

# Порт, который слушает gunicorn
GUNICORN_BIND_ADDR="127.0.0.1:8000"

##################################
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
##################################

log() {
  echo
  echo "===> $1"
  echo
}

##################################
# НАЧАЛО УСТАНОВКИ
##################################

log "1) Создание каталогов проекта"

mkdir -p "${APP_DIR}"
cd "${APP_DIR}"

log "2) Клонирование backend-репозитория (${BACKEND_REPO_URL})"

if [ -d "${BACKEND_DIR}" ]; then
  echo "Каталог ${BACKEND_DIR} уже существует, пропускаю git clone для backend."
else
  git clone "${BACKEND_REPO_URL}" "${BACKEND_DIR}"
fi

log "3) Клонирование frontend-репозитория (${FRONTEND_REPO_URL})"

if [ -d "${FRONTEND_DIR}" ]; then
  echo "Каталог ${FRONTEND_DIR} уже существует, пропускаю git clone для frontend."
else
  git clone "${FRONTEND_REPO_URL}" "${FRONTEND_DIR}"
fi

log "4) Backend: создание и активация virtualenv, установка зависимостей"

cd "${BACKEND_DIR}"

if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

# shellcheck disable=SC1091
source venv/bin/activate

pip install --upgrade pip
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
else
  echo "ВНИМАНИЕ: requirements.txt не найден, зависимости не установлены."
fi

log "5) Создание БД и пользователя PostgreSQL (${DB_NAME}, ${DB_USER})"

sudo -u postgres psql <<EOF
DO
\$do\$
BEGIN
   IF NOT EXISTS (
      SELECT
      FROM   pg_catalog.pg_roles
      WHERE  rolname = '${DB_USER}') THEN
      CREATE ROLE ${DB_USER} LOGIN PASSWORD '${DB_PASSWORD}';
   END IF;
END
\$do\$;

DO
\$do\$
BEGIN
   IF NOT EXISTS (
      SELECT
      FROM   pg_database
      WHERE  datname = '${DB_NAME}') THEN
      CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};
   END IF;
END
\$do\$;
EOF

log "6) Подготовка .env на основе .env.example (если есть)"

cd "${BACKEND_DIR}"

if [ -f ".env.example" ] && [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Скопирован .env из .env.example. ОТДЕЛЬНО проверь и отредактируй значения:"
  echo "- SECRET_KEY"
  echo "- DEBUG=False"
  echo "- ALLOWED_HOSTS=${DOMAIN},127.0.0.1"
  echo "- DB_ENGINE=django.db.backends.postgresql"
  echo "- DB_NAME=${DB_NAME}"
  echo "- DB_USER=${DB_USER}"
  echo "- DB_PASSWORD=${DB_PASSWORD}"
  echo "- DB_HOST=localhost"
  echo "- DB_PORT=5432"
else
  echo ".env.example не найден или .env уже существует — пропускаю копирование."
fi

log "7) Django: миграции и collectstatic"

cd "${BACKEND_DIR}"
# shellcheck disable=SC1091
source venv/bin/activate

if [ -f "manage.py" ]; then
  python manage.py migrate
  python manage.py collectstatic --noinput
else
  echo "manage.py не найден, миграции и collectstatic пропущены."
fi

log "8) Frontend: установка зависимостей и сборка"

cd "${FRONTEND_DIR}"

if [ -f "package-lock.json" ] || [ -f "package.json" ]; then
  if [ -f "package-lock.json" ]; then
    npm ci
  else
    npm install
  fi
  npm run build
else
  echo "package.json не найден, frontend-сборка пропущена."
fi

log "9) Копирование фронтенд-билда в ${NGINX_FRONT_ROOT}"

sudo mkdir -p "${NGINX_FRONT_ROOT}"
sudo chown -R "${LINUX_USER}:www-data" "${NGINX_FRONT_ROOT}"

if [ -d "${FRONTEND_DIR}/build" ]; then
  sudo rm -rf "${NGINX_FRONT_ROOT:?}/"*
  sudo cp -r "${FRONTEND_DIR}/build/"* "${NGINX_FRONT_ROOT}/"
else
  echo "Директория build не найдена, пропускаю копирование фронтенд-билда."
fi

log "10) Создание systemd unit для gunicorn: /etc/systemd/system/${PROJECT_NAME}.service"

sudo tee "/etc/systemd/system/${PROJECT_NAME}.service" >/dev/null <<EOF
[Unit]
Description=Gunicorn service for ${PROJECT_NAME}
After=network.target

[Service]
User=${LINUX_USER}
Group=www-data
WorkingDirectory=${BACKEND_DIR}
Environment="PATH=${BACKEND_DIR}/venv/bin"
ExecStart=${BACKEND_DIR}/venv/bin/gunicorn ${DJANGO_WSGI_MODULE}:application --bind ${GUNICORN_BIND_ADDR}
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "${PROJECT_NAME}.service"
sudo systemctl restart "${PROJECT_NAME}.service"

log "11) Создание конфига nginx: /etc/nginx/sites-available/${PROJECT_NAME}"

sudo tee "/etc/nginx/sites-available/${PROJECT_NAME}" >/dev/null <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    root ${NGINX_FRONT_ROOT};
    index index.html;

    location /static/ {
        alias ${BACKEND_DIR}/static/;
    }

    location /media/ {
        alias ${BACKEND_DIR}/media/;
    }

    location /api {
        proxy_pass http://${GUNICORN_BIND_ADDR};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location / {
        try_files \$uri /index.html;
    }
}
EOF

if [ ! -f "/etc/nginx/sites-enabled/${PROJECT_NAME}" ]; then
  sudo ln -s "/etc/nginx/sites-available/${PROJECT_NAME}" "/etc/nginx/sites-enabled/${PROJECT_NAME}"
fi

sudo nginx -t
sudo systemctl reload nginx

log "12) (Опционально) Установка SSL-сертификата через certbot"

echo "Для установки SSL выполни отдельно (после настройки DNS-домена):"
echo "  sudo certbot --nginx -d ${DOMAIN}"

log "Готово! Проверь приложение по адресу: http://${DOMAIN} (и https://${DOMAIN} после настройки SSL)."

