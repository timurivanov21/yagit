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
        commits_txt = " ".join(c["message"] for c in payload.get("commits", []))
        return event, branch, f"{branch} {commits_txt}"
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


async def apply_rule(
    rule: RuleDTO,
    issue_key: str,
    event_type: GitEventType,
    payload: dict,
):
    async with TrackerClient(
        token=rule.tracker_token,
        org_id=rule.tracker_org_id,
    ) as tr:
        await tr.move_issue(issue_key, rule.tracker_column_id)

        if event_type is GitEventType.PUSH:
            urls = [c["url"] for c in payload.get("commits", [])]
            if urls:
                await tr.add_comment(issue_key, "\n".join(urls))


def extract_issue_key(text: str) -> str | None:
    """
    Возвращает первый найденный ключ задачи (`ABC-123`) в *любом* регистре.

    ▸ Понимает названия веток `feature/PROJ-7-new-ui`, коммиты
      `Fix bug in proj-42`, тэги `#APP-8` или `[ab-1]`.

    ▸ Не чувствителен к регистру, на выходе всегда UPPERCASE.

    ▸ Если ключ не найден — возвращает `None`.
    """
    m = _ISSUE_RGX.search(text)
    return m.group(1).upper() if m else None
