from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from yagit.db.dependencies import get_db_session
from yagit.db.models.automation_rule import AutomationRule
from yagit.db.models.project import Project
from yagit.web.api.webhook.utils import _parse_event_type

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
    event_type, target_branch = _parse_event_type(payload)
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
            | (AutomationRule.target_branch.is_(None))       # «любая ветка»
        )

    rules = list((await session.execute(rules_stmt)).scalars())
    if not rules:
        return {"matched": 0}

    # for rule in rules:
    #     asyncio.create_task(
    #         _handle_rule(
    #             rule=rule,
    #             tracker_token=project.tracker_token,
    #             tracker_url=project.tracker_url,
    #             git_payload=payload,
    #         )
    #     )

    return {"accepted": len(rules)}
