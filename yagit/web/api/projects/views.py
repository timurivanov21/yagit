from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from yagit.db.dependencies import get_db_session
from yagit.db.models.project import Project

from .schema import ProjectCreate, ProjectRead

router = APIRouter()


@router.get("/", response_model=list[ProjectRead])
async def list_projects(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(Project))
    return result.scalars().all()


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate, session: AsyncSession = Depends(get_db_session),
):
    project = Project(**payload.dict())
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(project_id: int, session: AsyncSession = Depends(get_db_session)):
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found",
        )
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int, session: AsyncSession = Depends(get_db_session),
):
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found",
        )
    await session.delete(project)
    await session.commit()
