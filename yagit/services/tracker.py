import asyncio
from typing import Any, Dict, List, Optional

import httpx


class TrackerError(RuntimeError):
    """Базовая ошибка клиента."""


class TransitionNotFound(TrackerError):
    """Нет перехода из текущего статуса в требуемый."""


class IssueNotFound(TrackerError):
    """Задача не найдена."""


class TrackerClient:
    """
    Асинхронный мини-SDK для Yandex Tracker API v3.

    Примеры:
        async with TrackerClient(url, token, org_id) as tr:
            await tr.move_issue('PROJ-7', 'inProgress')
            await tr.add_comment('PROJ-7', 'Done in #abcd1234')

    Параметры:
        base_url     — `https://api.tracker.yandex.net` (по умолчанию).
        oauth_token  — персональный OAuth (scope `tracker`).
        org_id       — значение для заголовка `X-Org-ID` (или X-Cloud-Org-ID).
    """

    _MAX_RETRIES = 3
    _RETRY_STATUSES = {429, 502, 503, 504}

    def __init__(
        self,
        token: str,
        org_id: str,
        base_url: str = "https://api.tracker.yandex.net",
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._token = token
        self._org_id = org_id
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    # ─────────────── context manager ───────────────
    async def __aenter__(self) -> "TrackerClient":
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                # "Authorization": f"OAuth {self._token}",
                "Authorization": f"Bearer {self._token}",
                "X-Cloud-Org-ID": self._org_id,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Host": "api.tracker.yandex.net",
            },
            timeout=self._timeout,
        )
        return self

    async def __aexit__(self, *_) -> None:  # noqa: D401
        if self._client:
            await self._client.aclose()

    # ──────────────── helpers ────────────────
    async def _request(self, method: str, url: str, **kw) -> httpx.Response:
        """
        Универсальный запрос с back-off ретраями на 429/5xx.
        """
        assert self._client, "Use inside `async with TrackerClient`"
        for attempt in range(1, self._MAX_RETRIES + 1):
            resp = await self._client.request(method, url, **kw)
            if resp.status_code not in self._RETRY_STATUSES:
                break
            await asyncio.sleep(0.4 * attempt)  # expo-backoff
        if resp.status_code == 404:
            raise IssueNotFound(url)
        if resp.status_code >= 400:
            raise TrackerError(f"{resp.status_code}: {resp.text}")
        return resp

    # ─────────────── public API ───────────────
    async def list_columns(self, board_id: str) -> List[Dict[str, Any]]:
        r = await self._request("GET", f"/v3/boards/{board_id}/columns")
        return r.json()

    async def add_comment(self, issue_key: str, text: str) -> None:
        await self._request(
            "POST",
            f"/v3/issues/{issue_key}/comments",
            json={"text": text},
        )

    async def move_issue(self, issue_key: str, target_status: str) -> None:
        """
        Перемещает задачу в колонку / статус `target_status`
        (`status.id` **или** `status.key`).

        Алгоритм:
            1) GET /v3/issues/{issue}/transitions
            2) находим transition с нужным status
            3) POST /v3/issues/{issue}/transitions/{id}/_execute
        """
        transitions = await self._get_transitions(issue_key)
        transition_id = self._find_transition_id(transitions, target_status)
        await self._request(
            "POST",
            f"/v3/issues/{issue_key}/transitions/{transition_id}/_execute",
        )

    # ───────────── internal helpers ─────────────
    async def _get_transitions(self, issue_key: str) -> List[Dict[str, Any]]:
        r = await self._request("GET", f"/v3/issues/{issue_key}/transitions")
        return r.json()

    @staticmethod
    def _find_transition_id(
        transitions: List[Dict[str, Any]], target_status: str
    ) -> str:
        for tr in transitions:
            status = tr.get("to")
            if status.get("id") == target_status or status.get("key") == target_status:
                return tr["id"]
        raise TransitionNotFound(target_status)
