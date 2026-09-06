# API эндпоинты

Описание реализованных API-эндпоинтов проекта.

## Обратный звонок

### POST /api/callback-requests/

Создание запроса на обратный звонок.

**Тело запроса:**
```json
{
  "name": "Иван Иванов",
  "phone": "+7 (999) 123-45-67",
  "email": "ivan@example.com",
  "request_type": "individual",
  "comment": "Хочу уточнить даты потока"
}
```

Поля `email`, `request_type`, `comment` необязательны.  
`request_type`: `individual` | `organization`.

**Ответ 201:**
```json
{
  "id": 1,
  "name": "Иван Иванов",
  "phone": "+7 (999) 123-45-67",
  "email": "ivan@example.com",
  "request_type": "individual",
  "comment": "Хочу уточнить даты потока",
  "created_at": "2024-01-15T14:30:00Z"
}
```

При успешном создании отправляется email-уведомление на адрес из `NOTIFICATION_EMAIL`.  
Статус записи по умолчанию: `new`.

## Заявка слушателя

### POST /api/applications/

Создание заявки на программу.

**Тело запроса:**
```json
{
  "full_name": "Иван Иванов",
  "program": 1,
  "batch": null,
  "email": "ivan@example.com",
  "phone": "+7 (999) 123-45-67",
  "preferred_contact": "phone",
  "comment": ""
}
```

`batch`, `preferred_contact`, `comment` необязательны.  
`preferred_contact`: `phone` | `email` | `messenger`.

**Ответ 201:** объект заявки с `id`, `program_name`, `created_at`.  
Статус по умолчанию: `new`. Уведомление на `NOTIFICATION_EMAIL`.

## Корпоративный запрос

### POST /api/corporate-requests/

Создание запроса организации на коммерческое предложение.

**Тело запроса:**
```json
{
  "organization_name": "ООО Пример",
  "contact_name": "Анна Смирнова",
  "contact_position": "HR-директор",
  "phone": "+7 (999) 555-55-55",
  "email": "anna@example.com",
  "topics": "Управление проектами, бизнес-анализ",
  "employees_count": 25,
  "desired_dates": "осень 2026",
  "comment": "Нужна программа под ключ",
  "directions": [1],
  "programs": [2]
}
```

Обязательные поля: `organization_name`, `contact_name`, `phone`, `email`, `topics`, `employees_count`.  
`contact_position`, `desired_dates`, `comment`, `directions`, `programs` необязательны.

**Ответ 201:** созданный корпоративный запрос.  
Статус по умолчанию: `new`. Уведомление на `NOTIFICATION_EMAIL`.
