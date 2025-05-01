from yagit.db.models.automation_rule import GitEventType


def _parse_event_type(payload: dict) -> tuple[GitEventType | None, str | None]:
    """
    Определяем наш Enum-тип и, при необходимости, целевую ветку.
    Возвращаем (event_type | None, target_branch | None).
    """
    if payload.get("event_name") == "push" and payload.get("object_kind") == "push":
        before = payload.get("before", "")
        # all-zero SHA → это именно создание ветки
        is_create = before == "0000000000000000000000000000000000000000"
        event = GitEventType.BRANCH_CREATE if is_create else GitEventType.PUSH
        return event, payload["ref"].removeprefix("refs/heads/")
    if payload.get("event_type") == "merge_request" and payload.get("object_kind") == "merge_request":
        action = payload["object_attributes"]["action"]
        mapping = {
            "open": GitEventType.MERGE_REQUEST_OPENED,
            "merge": GitEventType.MERGE_REQUEST_MERGED,
            "close": GitEventType.MERGE_REQUEST_CLOSED,
        }
        event = mapping.get(action)
        tgt_branch = payload["object_attributes"]["target_branch"]
        return event, tgt_branch

    return None, None
