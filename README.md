# Expense Tracker

Простий web-застосунок для обліку витрат з інтеграцією Monobank API.

## Функціонал
- Додавання, редагування та видалення витрат
- Фільтрація за датою та категорією
- Синхронізація виписки з Monobank
- Збереження даних у PostgreSQL

## Технології
- Python (FastAPI)
- PostgreSQL
- SQLAlchemy
- Docker
- HTML / CSS / JavaScript

## Запуск

1. docker compose up -d
2. source ../venv/bin/activate
3. docker compose up db -d
4. uvicorn main:app --reload
5. Відкрити: http://127.0.0.1:8000/static/index.html
