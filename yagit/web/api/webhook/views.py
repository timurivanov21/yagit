from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from yagit.db.dependencies import get_db_session

router = APIRouter()


@router.post("/gitlab", status_code=202)
async def gitlab_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    body = await request.body()
    header_secret = request.headers.get("X-Gitlab-Token", "")
    # project = await find_project_by_secret(session, header_secret)
    # if not project:
    #     raise HTTPException(401, 'invalid secret')

    # дальше: парсим json, матчим правила, кладём задачу в background
    return {"received": True}
