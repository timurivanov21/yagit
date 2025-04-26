from pydantic import BaseModel, Field, field_validator

from yagit.db.models.automation_rule import GitEventType


class RuleBase(BaseModel):
    """Общая схема правила."""

    project_id: int = Field(..., ge=1)
    event_type: GitEventType = Field(..., description="Тип события GitLab")
    target_branch: str | None = Field(
        None,
        description="Целевая ветка (обязательно для MR‑событий)",
    )
    tracker_column_id: str = Field(..., description="ID колонки в Я.Трекере")
    tracker_column_name: str | None = Field(
        None,
        description="Название колонки (кеш, для UI)",
    )

    @field_validator("target_branch", mode="before")
    def branch_required_for_mr(cls, v, info):  # noqa: N805
        event: GitEventType = info.data.get("event_type")  # type: ignore[attr-defined]
        if event and event.is_merge and not v:
            raise ValueError("target_branch is required for merge request rules")
        return v


class RuleCreate(RuleBase):
    """Схема создания правила."""

    gitlab_project_id: int


class RuleRead(RuleBase):
    """Вывод правила."""

    id: int

    class Config:
        from_attributes = True
