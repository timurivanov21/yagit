
# Запуск и настройка окружения

## Требования

| Компонент | Версия |
|-----------|--------|
| Python    | 3.11+  |
| Docker    |  |

## Poetry

This project uses poetry. It's a modern dependency management
tool.

To run the project use this set of commands:

```bash
poetry install
poetry run python -m yagit
```


## Docker

You can start the project with docker using this command:

```bash
docker-compose up --build
```

If you want to develop in docker with autoreload and exposed ports add `-f deploy/docker-compose.dev.yml` to your docker command.
Like this:

```bash
docker-compose -f docker-compose.yml -f deploy/docker-compose.dev.yml --project-directory . up --build
```

This command exposes the web application on port 8000, mounts current directory and enables autoreload.

But you have to rebuild image every time you modify `poetry.lock` or `pyproject.toml` with this command:

```bash
docker-compose build
```

- API: <http://localhost:8000>
- Swagger: <http://localhost:8000/docs>
- PGAdmin: <http://localhost:5050>

## Running tests

If you want to run it in docker, simply run:

```bash
docker-compose run --build --rm api pytest -vv .
docker-compose down
```

For running tests on your local machine.
1. you need to start a database.

I prefer doing it with docker:
```
docker run -p "5432:5432" -e "POSTGRES_PASSWORD=yagit" -e "POSTGRES_USER=yagit" -e "POSTGRES_DB=yagit" postgres:16.3-bullseye
```


2. Run the pytest.
```bash
pytest -vv .
```
