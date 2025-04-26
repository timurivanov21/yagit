from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from yagit.web.api.webhooks.schema import GitlabPushPayload
from yagit.integrations.gitlab import handle_push_event

router = APIRouter()

@router.post("/gitlab")
async def gitlab_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    payload_dict = await request.json()

    try:
        payload = GitlabPushPayload(**payload_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")

    background_tasks.add_task(handle_push_event, payload)
    return {"status": "ok"}
