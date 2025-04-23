from fastapi.routing import APIRouter

from yagit.web.api import docs, projects, rules, webhooks

api_router = APIRouter()
api_router.include_router(docs.router)
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(rules.router,
    prefix="/projects/{project_id}/rules",
    tags=["Rules"],
)
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
