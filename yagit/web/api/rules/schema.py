from typing import Optional

from pydantic import BaseModel

from yagit.db.models.automation_rule import GitEventType


class RuleBase(BaseModel):
    event_type: GitEventType
    target_branch: Optional[str] = None
    target_column: str


class RuleCreate(RuleBase):
    """Схема создания правила."""


class RuleRead(RuleBase):
    id: int
    project_id: int

    class Config:
        orm_mode = True
