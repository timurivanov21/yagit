from pydantic import BaseModel

from yagit.db.models.automation_rule import GitEventType


class RuleBase(BaseModel):
    event_type: GitEventType
    target_branch: str | None = None
    tracker_column_id: str
    tracker_column_name: str | None = None


class RuleCreate(RuleBase):
    """Схема создания правила."""


class RuleRead(RuleBase):
    id: int
    project_id: int

    class Config:
        orm_mode = True
