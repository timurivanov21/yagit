from secrets import token_urlsafe

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from yagit.db.models.automation_rule import AutomationRule, GitEventType
from yagit.db.models.project import Project
from yagit.services.gitlab_client import GitLabClient
from yagit.settings import settings


def _compute_event_flags(rules: list[AutomationRule]) -> dict[str, bool]:
    """Вернуть dict флагов для GitLab‑хук‑создания."""

    push_events = any(r.event_type == GitEventType.BRANCH_CREATE for r in rules)
    merge_events = any(r.event_type.is_merge for r in rules)
    return {
        "push_events": push_events,
        "merge_requests_events": merge_events,
    }


async def _sync_webhook(
    session: AsyncSession,
    project: Project,
    gitlab_project_id: int,
) -> None:
    """Создать или обновить веб‑хук проекта в соответствии с текущими правилами."""

    rules_stmt = select(AutomationRule).where(AutomationRule.project_id == project.id)
    rules = list((await session.execute(rules_stmt)).scalars().all())
    events_payload = _compute_event_flags(rules)

    if not project.gitlab_webhook_secret:
        project.gitlab_webhook_secret = token_urlsafe(settings.webhook_secret_length)
        await session.commit()
    webhook_url = f"{settings.backend_public_url}/api/webhook/gitlab"

    async with GitLabClient(project.gitlab_token) as gl:
        await gl.ensure_hook(
            project_id=gitlab_project_id,
            url=webhook_url,
            secret_token=project.gitlab_webhook_secret,
            hook_payload=events_payload,
        )
