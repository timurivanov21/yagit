from enum import StrEnum

from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Enum

from yagit.db.base import Base
from yagit.db.models.mixins import TimestampMixin


class GitEventType(StrEnum):
    """GitLab события, на которые можно реагировать в правилах."""

    BRANCH_CREATE = "branch_create"
    PUSH = "push"
    MERGE_REQUEST_OPENED = "merge_request_opened"
    MERGE_REQUEST_MERGED = "merge_request_merged"
    MERGE_REQUEST_CLOSED = "merge_request_closed"

    @property
    def is_merge(self) -> bool:
        return self.name.startswith("MERGE_REQUEST")


class AutomationRule(TimestampMixin, Base):
    """Правило автоматизации перемещения карточек по событиям GitLab."""

    __tablename__ = "automation_rules"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "event_type",
            "target_branch",
            name="uq_rule_per_project_event_branch",
        ),
    )

    id: int = Column(Integer, primary_key=True, index=True)
    project_id: int = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    event_type: GitEventType = Column(
        Enum(GitEventType),
        nullable=False,
        index=True,
    )
    target_branch: str | None = Column(String(255), nullable=True)
    tracker_column_id: str = Column(String(64), nullable=False)
    project = relationship("Project", back_populates="rules")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            "<AutomationRule id={0.id} project_id={0.project_id} "
            "event={0.event_type} branch={0.target_branch!r}>"
        ).format(self)
