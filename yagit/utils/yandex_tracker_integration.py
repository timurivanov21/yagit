import httpx
from yagit.settings import settings

HEADERS = {
    "Authorization": f"OAuth {settings.TRACKER_TOKEN}",
    "X-Org-ID": settings.TRACKER_ORG_ID,
    "Content-Type": "application/json"
}

API_URL = "https://api.tracker.yandex.net/v2"


async def update_tracker_status(issue_id: str, status: str):
    url = f"{API_URL}/issues/{issue_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.patch(url, headers=HEADERS, json={"status": status})
        if resp.status_code >= 300:
            print(f"[ERROR] Не удалось обновить статус задачи {issue_id}: {resp.text}")


async def add_task_comment(issue_id: str, text: str):
    url = f"{API_URL}/issues/{issue_id}/comments"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=HEADERS, json={"text": text})
        if resp.status_code >= 300:
            print(f"[ERROR] Не удалось добавить комментарий в {issue_id}: {resp.text}")
