## SETUP_DJANGO_APP

Тестовая инструкция по стартовой установке Django-приложения (backend + frontend) на **Ubuntu/Debian** без Docker.
Приложение разворачивается в домашнем каталоге пользователя в структуре:

- `~/PROJECT_NAME/backend`
- `~/PROJECT_NAME/frontend`

Во всех командах ниже **замени плейсхолдеры ЗАГЛАВНЫМИ_БУКВАМИ** на свои значения:
`PROJECT_NAME`, `BACKEND_REPO_URL`, `FRONTEND_REPO_URL`, `DOMAIN`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` и т.д.

---

### 0. Подключение по SSH

- Подключись к серверу:

  ```bash
  ssh nnd@84.252.140.25
  ```

- Убедись, что пользователь может выполнять `sudo`:

  ```bash
  sudo whoami  # должно вывести 'root'
  ```

---

### 1. Обновление системы и установка базовых пакетов

```bash
sudo apt update && sudo apt upgrade -y

sudo apt install -y \
  git python3 python3-venv python3-pip \
  nginx postgresql postgresql-contrib \
  nodejs npm \
  certbot python3-certbot-nginx
```

При необходимости дополнительно установи `build-essential` и dev-библиотеки для сборки Python-зависимостей.

---

### 2. Создание директории проекта

Выберем каталог проекта в домашней директории пользователя:

```bash
mkdir -p ~/PROJECT_NAME
cd ~/PROJECT_NAME
```

В дальнейшем структура будет такой:

- `~/PROJECT_NAME/backend` — Django backend;
- `~/PROJECT_NAME/frontend` — frontend (SPA/React/Vue и т.п.).

---

### 3. Клонирование backend-репозитория

```bash
cd ~/PROJECT_NAME
git clone BACKEND_REPO_URL backend
```

Пример:

```bash
git clone git@github.com:yourname/your-backend-repo.git backend
```

---

### 4. Клонирование frontend-репозитория

```bash
cd ~/PROJECT_NAME
git clone FRONTEND_REPO_URL frontend
```

Пример:

```bash
git clone git@github.com:yourname/your-frontend-repo.git frontend
```

---

### 5. Настройка backend: virtualenv и зависимости

```bash
cd ~/PROJECT_NAME/backend

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

---

### 6. Создание БД и пользователя PostgreSQL

Выполни команды для создания пользователя и базы (замени имена и пароль):

```bash
sudo -u postgres psql
```

Внутри `psql`:

```sql
CREATE USER DB_USER WITH PASSWORD 'DB_PASSWORD';
CREATE DATABASE DB_NAME OWNER DB_USER;
GRANT ALL PRIVILEGES ON DATABASE DB_NAME TO DB_USER;
\q
```

Рекомендуется, чтобы `DB_NAME` и `DB_USER` совпадали с именем проекта (например, `project_name`).

---

### 7. Копирование и заполнение `.env`

В backend уже есть файл `.env.example`. Скопируй его в `.env`:

```bash
cd ~/PROJECT_NAME/backend
cp .env.example .env
```

Открой `.env` и пропиши реальные значения:

- **SECRET_KEY** — сгенерируй новый ключ:

  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```

- **DEBUG** — для продакшена поставить `False`.
- **ALLOWED_HOSTS** — домен и/или IP сервера, через запятую (например, `example.com,127.0.0.1`).
- **Блок PostgreSQL** — раскомментируй и заполни строки:

  ```env
  DB_ENGINE=django.db.backends.postgresql
  DB_NAME=DB_NAME
  DB_USER=DB_USER
  DB_PASSWORD=DB_PASSWORD
  DB_HOST=localhost
  DB_PORT=5432
  ```

Убедись, что SQLite-конфиг (если есть) закомментирован, если ты переходишь на PostgreSQL.

---

### 8. Миграции и collectstatic

С активированным виртуальным окружением:

```bash
cd ~/PROJECT_NAME/backend
source venv/bin/activate

python manage.py migrate
python manage.py collectstatic
```

При запросе подтверждения от `collectstatic` ответь `yes`.

---

### 9. Настройка frontend: установка и сборка

```bash
cd ~/PROJECT_NAME/frontend

npm install        # или npm ci, если используешь lock-файл
npm run build
```

Предположим, что сборка попадает в директорию `build`. Настроим директорию, откуда nginx будет раздавать статику фронта:

```bash
sudo mkdir -p /var/www/PROJECT_NAME
sudo chown -R nnd:nnd /var/www/PROJECT_NAME

cp -r build/* /var/www/PROJECT_NAME/
```

Если у твоего фронта другая структура (например, `dist`), поправь путь.

---

### 10. Настройка gunicorn

Убедись, что в `requirements.txt` есть `gunicorn` (или установи его):

```bash
cd ~/PROJECT_NAME/backend
source venv/bin/activate

pip install gunicorn
```

Предположим, что Django-проект использует модуль `DJANGO_WSGI_MODULE`, например `config.wsgi:application` или `project_name.wsgi:application`.

Проверь запуск gunicorn вручную:

```bash
gunicorn DJANGO_WSGI_MODULE:application --bind 127.0.0.1:8000
```

Если сервер успешно стартует, останови его (Ctrl+C) и переходи к настройке systemd.

#### 10.1. Systemd unit для gunicorn

Создай unit-файл (от root):

```bash
sudo nano /etc/systemd/system/PROJECT_NAME.service
```

Пример содержимого:

```ini
[Unit]
Description=Gunicorn service for PROJECT_NAME
After=network.target

[Service]
User=nnd
Group=www-data
WorkingDirectory=/home/nnd/PROJECT_NAME/backend
Environment="PATH=/home/nnd/PROJECT_NAME/backend/venv/bin"
ExecStart=/home/nnd/PROJECT_NAME/backend/venv/bin/gunicorn DJANGO_WSGI_MODULE:application --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Активируй сервис:

```bash
sudo systemctl daemon-reload
sudo systemctl enable PROJECT_NAME.service
sudo systemctl start PROJECT_NAME.service
sudo systemctl status PROJECT_NAME.service
```

Статус должен быть `active (running)`.

---

### 11. Настройка nginx

Создай конфиг nginx (как root):

```bash
sudo nano /etc/nginx/sites-available/PROJECT_NAME
```

Пример конфига (SPA-фронт + Django API под `/api`):

```nginx
server {
    listen 80;
    server_name DOMAIN;

    root /var/www/PROJECT_NAME;
    index index.html;

    location /static/ {
        alias /home/nnd/PROJECT_NAME/backend/static/;
    }

    location /media/ {
        alias /home/nnd/PROJECT_NAME/backend/media/;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri /index.html;
    }
}
```

Включи сайт и перезапусти nginx:

```bash
sudo ln -s /etc/nginx/sites-available/PROJECT_NAME /etc/nginx/sites-enabled/PROJECT_NAME

sudo nginx -t
sudo systemctl reload nginx
```

---

### 12. Установка SSL (Let’s Encrypt, certbot)

Убедись, что DNS-записи домена указывают на IP сервера. Затем запусти certbot:

```bash
sudo certbot --nginx -d DOMAIN
```

При необходимости можно указать несколько доменов:

```bash
sudo certbot --nginx -d example.com -d www.example.com
```

Certbot сам пропишет HTTPS-конфиг и настроит автоматическое продление сертификатов.

Проверить таймер продления:

```bash
sudo systemctl status certbot.timer
```

---

### 13. Проверка и отладка

- Проверка статуса сервиса gunicorn:

  ```bash
  sudo systemctl status PROJECT_NAME.service
  ```

- Логи сервиса:

  ```bash
  journalctl -u PROJECT_NAME.service -e
  ```

- Проверка nginx:

  ```bash
  sudo nginx -t
  sudo systemctl status nginx
  ```

- Проверка API с сервера:

  ```bash
  curl http://127.0.0.1:8000/
  ```

- Проверка сайта извне: открыть `http://DOMAIN` и `https://DOMAIN` в браузере.

---

### 14. Расширения (что можно добавить позже)

- Интеграция с CI (GitHub Actions / GitLab CI), чтобы после пуша в основную ветку автоматически запускались тесты и деплой.
- Настройка резервного копирования БД (cron + `pg_dump`).
- Скрипт деплоя для обновлений после стартовой установки (pull, migrate, collectstatic, reload gunicorn/nginx).

