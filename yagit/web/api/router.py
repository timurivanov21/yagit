from fastapi.routing import APIRouter

from yagit.web.api import docs, projects, rules, webhook, webhooks

api_router = APIRouter()
api_router.include_router(docs.router)
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(webhook.router, prefix="/webhook", tags=["Webhooks"])
api_router.include_router(
    rules.router,
    prefix="/projects/{project_id}/rules",
    tags=["Rules"],
)
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
