import asyncio

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from yagit.db.dependencies import get_db_session
from yagit.db.models.automation_rule import AutomationRule
from yagit.db.models.project import Project
from yagit.web.api.webhook.schema import RuleDTO
from yagit.web.api.webhook.utils import _parse_event_type, apply_rule, extract_issue_key

router = APIRouter()


@router.post("/gitlab", status_code=status.HTTP_202_ACCEPTED)
async def gitlab_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    secret = request.headers.get("X-Gitlab-Token", "")
    if not secret:
        raise HTTPException(status_code=401, detail="Missing X-Gitlab-Token")

    project_stmt = select(Project).where(Project.gitlab_webhook_secret == secret)
    project = (await session.execute(project_stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=401, detail="Invalid secret token")

    payload = await request.json()
    event_type, target_branch, search_text = _parse_event_type(payload)
    if event_type is None:
        return {"skipped": True}

    rules_stmt = select(AutomationRule).where(
        AutomationRule.project_id == project.id,
        AutomationRule.event_type == event_type,
    )
    if event_type.name.startswith("MR_"):
        # если правило указало конкретную ветку — матчим строго
        rules_stmt = rules_stmt.where(
            (AutomationRule.target_branch == target_branch)  # exact match
            | (AutomationRule.target_branch.is_(None))  # «любая ветка»
        )

    rows = list((await session.execute(rules_stmt)).scalars())
    if not rows:
        return {"matched": 0}
    rule_dtos = [RuleDTO(
        id=row.id,
        tracker_column_id=row.tracker_column_id,
        tracker_token=row.project.tracker_token,
        tracker_org_id=row.project.tracker_org_id,
    ) for row in rows]

    issue_key = extract_issue_key(search_text)
    if not issue_key:
        return {"matched": 0, "reason": "no issue key"}

    await asyncio.gather(
        *(
            apply_rule(
                r,
                issue_key,
                event_type,
                payload,
            )
            for r in rule_dtos
        )
    )

    return {"accepted": len(rule_dtos)}
