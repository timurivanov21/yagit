import hmac
from typing import Any

import httpx

from yagit.web.api.projects.schema import GitLabProject


class GitLabClient:
    def __init__(
        self,
        token: str,
        *,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = "https://gitlab.com"
        self._client = httpx.AsyncClient(
            base_url=f"{self.base_url}/api/v4",
            timeout=timeout,
            headers={
                "PRIVATE-TOKEN": token,
                "Content-Type": "application/json",
            },
        )

    async def _get(self, url: str, **kwargs):
        resp = await self._client.get(url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    async def _post(self, url: str, **kwargs):
        resp = await self._client.post(url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    async def _put(self, url: str, **kwargs):
        resp = await self._client.put(url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    async def get_project(self, project_id: int) -> dict[str, Any]:
        return await self._get(f"/projects/{project_id}")

    async def list_branches(self, project_id: int) -> list[str]:
        branches = await self._get(f"/projects/{project_id}/repository/branches")
        return [b["name"] for b in branches]

    async def list_hooks(self, project_id: int) -> list[dict[str, Any]]:
        return await self._get(f"/projects/{project_id}/hooks")

    async def list_projects(self) -> list[GitLabProject]:
        """Возвращает список проектов, доступных токену."""
        params = {
            "archived": "false",
            "owned": "true",
            "simple": "true",
        }
        resp = await self._get("/projects", params=params)
        projects: list[GitLabProject] = []
        for project in resp:
            projects.append(
                GitLabProject(
                    gitlab_project_id=project.get("id"),
                    name=project.get("name"),
                ),
            )
        return projects

    async def ensure_hook(
        self,
        project_id: int,
        url: str,
        secret_token: str,
        hook_payload: dict,
    ):
        """Создаёт или обновляет хук под нужные события.

        :param project_id: numeric id проекта в GitLab
        :param url: публичный URL вашего эндпоинта
        :param secret_token: токен, который GitLab будет присылать в заголовке
        :param hook_payload: настройки хука
        """
        hooks = await self.list_hooks(project_id)
        hook_id = None
        for hook in hooks:
            if hook.get("url") == url:
                hook_id = hook["id"]
                break

        payload = {
            "url": url,
            "token": secret_token,
        }
        payload.update(**hook_payload)
        if hook_id is None:
            await self._client.post(f"/projects/{project_id}/hooks", json=payload)
        else:
            await self._client.put(
                f"/projects/{project_id}/hooks/{hook_id}",
                json=payload,
            )

    @staticmethod
    def verify_gitlab_token(header_token: str, expected: str) -> bool:
        """Сравниваем полученный токен с тем, что хранится у нас в БД."""
        return hmac.compare_digest(header_token or "", expected or "")

    async def close(self) -> None:
        """Закрыть underlying httpx.AsyncClient"""
        await self._client.aclose()

    async def __aenter__(self) -> "GitLabClient":
        return self

    async def __aexit__(self, *exc):  # type: ignore[no-untyped-def]
        await self.close()
