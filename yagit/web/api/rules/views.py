from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from yagit.db.dependencies import get_db_session
from yagit.db.models.automation_rule import AutomationRule
from yagit.db.models.project import Project
from yagit.web.api.rules.schema import RuleCreate, RuleRead

router = APIRouter()


@router.get("/", response_model=list[RuleRead])
async def list_rules(project_id: int, session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(
        select(AutomationRule).where(AutomationRule.project_id == project_id),  # type: ignore
    )
    return result.scalars().all()


@router.post("/", response_model=RuleRead, status_code=status.HTTP_201_CREATED)
async def create_rule(
    project_id: int,
    payload: RuleCreate,
    session: AsyncSession = Depends(get_db_session),
):
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    rule = AutomationRule(project_id=project_id, **payload.dict())
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
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
