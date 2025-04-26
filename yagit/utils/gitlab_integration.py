import re
from yagit.utils.yandex_tracker_integration import update_tracker_status, add_task_comment
from yagit.api.webhooks.schema import GitlabPushPayload

TASK_ID_REGEX = re.compile(r"\b([A-Z]+-\d+)\b")

def extract_task_ids(text: str) -> list[str]:
    return TASK_ID_REGEX.findall(text)


async def handle_push_event(payload: GitlabPushPayload):
    ref = payload.ref
    before = payload.before
    created = payload.created
    commits = payload.commits or []

    for commit in commits:
        task_ids = extract_task_ids(commit.message)
        for task_id in task_ids:
            text = f"Новый коммит:\n{commit.message}\n Ссылка: {commit.url}"
            await add_task_comment(task_id, text)
