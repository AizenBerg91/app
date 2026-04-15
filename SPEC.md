# Model Catalog - Specification

## Project Overview
- **Project Name**: Model Catalog
- **Type**: Web Application (Docker)
- **Port**: 4444
- **Core Functionality**: CRUD каталог моделей с аватарами, фото, видео, тегами и поиском
- **Target Users**: Администраторы каталога моделей

## Tech Stack
- Backend: Node.js + Express
- Database: SQLite (встроенная)
- Frontend: HTML/CSS/JS (Vanilla SPA)
- Docker + Docker Compose

## Functionality

### Features
1. **Просмотр каталога**: Сетка карточек с аватарами
2. **Поиск**: Фильтрация по имени и тегам в реальном времени
3. **Добавление модели**: Модальная форма с загрузкой фото
4. **Редактирование модели**: Изменение всех полей
5. **Удаление модели**: С подтверждением
6. **Теги**: Добавление/удаление тегов для каждой модели
7. **Фильтрация по тегам**: Боковая панель с чекбоксами

### API Endpoints
- GET /api/models - Список всех моделей
- GET /api/models/:id - Одна модель
- POST /api/models - Создать
- PUT /api/models/:id - Обновить
- DELETE /api/models/:id - Удалить
- GET /api/tags - Список всех тегов
- POST /api/upload - Загрузка файлов