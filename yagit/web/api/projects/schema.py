from typing import TYPE_CHECKING, List

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from yagit.web.api.rules.schema import RuleRead


class ProjectBase(BaseModel):
    name: str = Field(..., max_length=255)
    gitlab_url: str
    gitlab_token: str
    tracker_url: str
    tracker_token: str


class ProjectCreate(ProjectBase):
    """Схема создания проекта."""


class ProjectRead(ProjectBase):
    id: int

    class Config:
        orm_mode = True


class ProjectReadWithRules(ProjectRead):
    rules: List["RuleRead"] = []
