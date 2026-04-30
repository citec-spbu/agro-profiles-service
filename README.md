# agro-profiles-service

Микросервис пользовательских профилей и настроек.

## Стек
- Python 3.11
- FastAPI
- PostgreSQL
- SQLAlchemy v2

## Быстрый запуск
```bash
docker network create agronetwork 2>/dev/null || true
docker compose up -d --build
```

Сервис доступен на `http://localhost:8002`, Swagger - `http://localhost:8002/docs`.
База данных доступна на `localhost:5435`.

## Миграции
```bash
docker compose run --rm migrations
```

## Переменные окружения
Конфигурация хранится в `.env` и используется всеми контейнерами сервиса.
