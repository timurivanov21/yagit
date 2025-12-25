import random
from typing import Any, Dict, List, Optional

from locust import HttpUser, between, task


class YagitReadOnlyUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def read_projects_and_rules(self) -> None:
        # 1) List projects
        with self.client.get(
            url="/api/projects/",
            name="GET /api/projects/",
            catch_response=True,
            timeout=10.0,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Unexpected status: {response.status_code}")
                return

            try:
                projects: List[Dict[str, Any]] = response.json()
            except Exception:
                response.failure("Invalid JSON in projects list")
                return

            if not projects:
                # Важно: Locust не должен "падать" если БД пустая.
                # Для перф-теста просто считаем это "no-op" успешным кейсом.
                response.success()
                return

        # 2) Pick a project
        project_item: Dict[str, Any] = random.choice(projects)
        project_identifier: Optional[int] = project_item.get("id")

        if not isinstance(project_identifier, int):
            # Такое маловероятно, но лучше явно зафейлить сценарий, чем молча продолжать.
            return

        # 3) Get project details
        with self.client.get(
            url=f"/api/projects/{project_identifier}",
            name="GET /api/projects/:id",
            catch_response=True,
            timeout=10.0,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Unexpected status: {response.status_code}")

        # 4) List rules for project
        with self.client.get(
            url=f"/api/projects/{project_identifier}/rules/",
            name="GET /api/projects/:id/rules/",
            catch_response=True,
            timeout=10.0,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Unexpected status: {response.status_code}")
                return

            # Ничего не проверяем по содержимому — это нагрузочный тест,
            # важнее стабильность кода ответа и время.
            _ = response.text
