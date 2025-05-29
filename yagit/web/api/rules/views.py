from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from yagit.db.dependencies import get_db_session
from yagit.db.models.automation_rule import AutomationRule
from yagit.db.models.project import Project
from yagit.web.api.rules.schema import RuleCreate, RuleRead
from yagit.web.api.rules.utils import _sync_webhook

router = APIRouter()


@router.get("/", response_model=list[RuleRead])
async def list_rules(project_id: int, session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(
        select(AutomationRule).where(AutomationRule.project_id == project_id),  # type: ignore
    )
    return result.scalars().all()


@router.post("/", response_model=RuleRead, status_code=status.HTTP_201_CREATED)
async def create_rule(
    payload: RuleCreate,
    project_id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_db_session),
):
    """Создать правило автоматизации и синхронизировать веб‑хук GitLab."""

    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.tracker_board_id = payload.tracker_board_id
    project.tracker_column_id = payload.tracker_column_id

    dup_stmt = select(AutomationRule).where(
        and_(
            AutomationRule.project_id == project_id,
            AutomationRule.event_type == payload.event_type,
            AutomationRule.target_branch == payload.target_branch,
        ),
    )
    dup_rule = (await session.execute(dup_stmt)).scalar_one_or_none()
    if dup_rule:
        raise HTTPException(status_code=409, detail="Rule already exists")

    rule = AutomationRule(
        project_id=project_id,
        event_type=payload.event_type,
        target_branch=payload.target_branch,
        tracker_column_id=payload.tracker_column_id,
    )
    session.add(rule)
    await session.commit()
    await session.refresh(rule)

    await _sync_webhook(session, project, payload.gitlab_project_id)
    project.gitlab_project_id = payload.gitlab_project_id
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    project_id: int,
    rule_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    rule = await session.get(AutomationRule, rule_id)
    if not rule or rule.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found",
        )
    await session.delete(rule)
    await session.commit()
