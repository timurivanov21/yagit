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


class ProjectRead(BaseModel):
    id: int
    name: str = Field(..., max_length=255)

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
