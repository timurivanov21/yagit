from typing import TYPE_CHECKING, List

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from yagit.web.api.rules.schema import RuleRead


class ProjectBase(BaseModel):
    name: str = Field(..., max_length=255)
    gitlab_token: str
    tracker_token: str
    tracker_org_id: str


class ProjectCreate(ProjectBase):
    """Схема создания проекта."""

class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    tracker_token: str | None = None
    tracker_org_id: str | None = None
    tracker_board_id: int | None = None
    gitlab_token: str | None = None
    gitlab_webhook_secret: str | None = None
    gitlab_project_id: int | None = None


class ProjectRead(BaseModel):
    id: int
    name: str = Field(..., max_length=255)
    gitlab_project_id: int | None = None

    class Config:
        orm_mode = True


class ProjectReadWithRules(ProjectRead):
    rules: List["RuleRead"] = []


class TokenIn(BaseModel):
    access_token: str = Field(..., description="GitLab personal / project token")


class GitLabProject(BaseModel):
    gitlab_project_id: int
    name: str


class ProjectsResponse(BaseModel):
    repositories: list[GitLabProject]
    project_id: int


class WebhookPayload(BaseModel):
    project_id: int
    gitlab_project_id: int


class TrackerColumn(BaseModel):
    id: str
    name: str


class TrackerBoard(BaseModel):
    id: int
    name: str
    columns: List[TrackerColumn]
