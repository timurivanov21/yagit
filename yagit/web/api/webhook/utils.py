import re

from yagit.db.models.automation_rule import GitEventType
from yagit.services.tracker import TrackerClient
from yagit.web.api.webhook.schema import RuleDTO

_ISSUE_RGX = re.compile(
    r"(?:^|[^A-Z0-9])"        # начало строки или не-алфавитно-цифровой символ
    r"([A-Z][A-Z0-9]+-\d+)"   # собственно ключ задачи
    r"(?:$|[^A-Z0-9])",       # конец или не-алфавитно-цифровой символ
    flags=re.IGNORECASE,
)


def _parse_event_type(payload: dict) -> tuple[GitEventType | None, str | None, str]:
    """
    Определяем наш Enum-тип и, при необходимости, целевую ветку.
    Возвращаем (event_type | None, target_branch | None).
    """
    if payload.get("event_name") == "push" and payload.get("object_kind") == "push":
        before = payload.get("before", "")
        # all-zero SHA → это именно создание ветки
        is_create = before == "0000000000000000000000000000000000000000"
        branch = payload["ref"].removeprefix("refs/heads/")
        event = GitEventType.BRANCH_CREATE if is_create else GitEventType.PUSH
        return event, branch, branch
    if payload.get("event_type") == "merge_request" and payload.get("object_kind") == "merge_request":
        action = payload["object_attributes"]["action"]
        mapping = {
            "open": GitEventType.MERGE_REQUEST_OPENED,
            "merge": GitEventType.MERGE_REQUEST_MERGED,
            "close": GitEventType.MERGE_REQUEST_CLOSED,
        }
        event = mapping.get(action)
        tgt_branch = payload["object_attributes"]["target_branch"]
        src = payload["object_attributes"]["source_branch"]
        return event, tgt_branch, src

    return None, None, ""
