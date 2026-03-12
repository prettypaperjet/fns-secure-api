# Secure Gateway API

Защищенный асинхронный шлюз на FastAPI для обмена юридически значимыми сообщениями (банковскими гарантиями, квитками) между финансовыми реестрами.

## 📌 Описание проекта
Проект реализует защищенный прием, криптографическую проверку и хранение пакетов данных. Обмен построен на архитектуре вложенных структур, где каждый слой сериализуется в JSON и кодируется в Base64. 

**Ключевой функционал:**
* Автоматическая распаковка многослойных транспортных конвертов (`SignedApiData`).
* Строгая проверка целостности данных путем вычисления и сверки криптографических хэшей SHA-256.
* Сохранение валидных транзакций в реляционную базу данных PostgreSQL.
* Автоматическая генерация, подписание и возврат ответных технологических транзакций (Квиток о получении, тип 215) в рамках одного HTTP-цикла.
* Поиск и фильтрация исходящих сообщений с поддержкой пагинации (Limit/Offset).




## Структура проекта

```text
├── migrations/          
├── routers/
│   └── messages.py      # Эндпоинты API (incoming, outgoing)
├── config.py            # Настройки проекта
├── database.py          # Подключение к БД PostgreSQL 
├── docker-compose.yaml  
├── Dockerfile           
├── main.py              
├── models.py            # ORM модели SQLAlchemy
├── schemas.py           # Pydantic схемы для строгой валидации
├── test_api.py          # Скрипт для тестирования криптографии
└── utils.py             # Вспомогательные утилиты (хэширование SHA-256, Base64)
```

## Примеры запросов

### Получение исходящих сообщений

```bash
curl -X POST http://localhost:8000/api/messages/outgoing \
  -H "Content-Type: application/json" \
  -d '{
  "Data": "eyJTdGFydERhdGUiOiAiMjAyNi0wMy0wMVQwMDowMDowMFoiLCAiRW5kRGF0ZSI6ICIyMDI2LTAzLTMxVDIzOjU5OjU5WiIsICJMaW1pdCI6IDEwLCAiT2Zmc2V0IjogMH0=",
  "Sign": "U0lHTkFUVVJF",
  "SignerCert": "U1lTVEVNX0E="
}'
```

### Прием входящих сообщений

```bash
curl -X POST http://localhost:8000/api/messages/incoming \
  -H "Content-Type: application/json" \
  -d '{
  "Data": "eyJUcmFuc2FjdGlvbnMiOlt7IlRyYW5zYWN0aW9uIFR5cGUiOjEsIkRhdGEiOiJleUoyYVdSMGFYQnBZMkYwYVc5dUlqb2lVMkZ0Y0d4bElpd2laWGhoYlhCc1pTSTZJbUpoYzJVdFkyOXVkR2hoYm1SaFkyVWlMQ0pqYUdGcGJsZDFhV1FpT2lJd01qTTRNMlV0T0RRMU55MDBZelpoTFRreVpqZ3ROall6TUdFMVl6WTFaRFVpZlE9PSIsIkhhc2giOiI4QzBBQ0JGMzdBRTIxNEFEMTk0MjYxMDVDRkFEQjA5MzY4RUFDRjFCRTIyMzg4NkY0MTA3RjAxMjBFNzQ5NkMwIiwiU2lnbiI6IiIsIlNpZ25lckNlcnQiOiJVMWxUVkVWTlgwRT0iLCJUcmFuc2FjdGlvbiBUaW1lIjoiMjAyNi0wMy0xM1QwMDowMDowMFoiLCJNZXRhZGF0YSI6bnVsbCwiVHJhbnNhY3Rpb25JbiI6bnVsbCwiVHJhbnNhY3Rpb25PdXQiOm51bGx9XSwiQ291bnQiOjF9",
  "Sign": "U0lHTkFUVVJF",
  "SignerCert": "U1lTVEVNX0E="
}'
```



## Quick Start
### С Docker (рекомендуется)
```bash
# Клонировать репозиторий
git clone https://github.com/prettypaperjet/fns-secure-api.git
cd fns-secure-api

# Создать .env
cp .env.example .env
# Отредактируйте .env под ваши значения

# Запустить все сервисы
docker-compose up --build
```

Сервис будет доступен по адресу: http://localhost:8000

### Локально (без Docker)

Для локального запуска убедитесь, что у вас установлен и запущен сервер **PostgreSQL**, а также создана пустая база данных для проекта.

```bash
# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux / Mac
venv\Scripts\activate     # Windows

# Установить зависимости
pip install -r requirements.txt

# Настроить переменные окружения
cp .env.example .env
# ВНИМАНИЕ: Обязательно отредактируйте .env, указав доступ к вашей локальной БД.
# Пример: DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fns_db

# Применить миграции (создать таблицы в базе данных)
alembic upgrade head

# Запустить приложение
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```




