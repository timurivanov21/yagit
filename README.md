
# YaGit

**Интеграция GitLab Webhook‑ов с Яндекс.Трекером.**

YaGit автоматически отслеживает события *branch*, *push* и *merge request* в GitLab и в соответствии с настройками перемещает задачи в Яндекс.Трекере, добавляет комментарии и меняет статусы.

## Возможности

- **CRUD-панель проектов** с хранением GitLab URL и OAuth‑токена Трекера
- **Гибкие правила** «*событие → колонка / комментарий*», настраиваемые через REST API
- **Webhook** `/api/webhook/gitlab` с ответом `202 Accepted`
- **Асинхронный FastAPI‑backend** и очереди `asyncio`
- **PostgreSQL + SQLAlchemy 2.0** для хранения правил, проектов и истории
- **OpenAPI (Swagger UI)** по адресу `/docs`

Документация:

| Раздел | Ссылка |
|--------|--------|
| Архитектура | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Дизайн и UX | [docs/DESIGN.md](docs/DESIGN.md) |
| Запуск и окружение | [docs/SETUP.md](docs/SETUP.md) |

---

## Быстрый старт

```bash
git clone https://github.com/timurivanov21/yagit.git
cd yagit
docker-compose up --build   
```

Откройте <http://localhost:8000/docs> и проверьте, что API доступно.

Для подробных инструкций смотрите [docs/SETUP.md](docs/SETUP.md).

---

## Вклад и разработка

1. **Fork** и `git clone` вашего форка
2. `git remote add upstream https://github.com/timurivanov21/yagit.git`
3. `git checkout -b feature/<summary>`
4. Коммиты в стиле *Conventional Commits*
5. **Pull Request** в `main` апстрима

Подробный гайд: [CONTRIBUTING.md](docs/CONTRIBUTING.md).
