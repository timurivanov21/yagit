from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from yagit.db.base import Base
from yagit.db.models.mixins import TimestampMixin


class Project(TimestampMixin, Base):
    """Интегрируемый проект GitLab ↔ Яндекс.Трекер."""

    __tablename__ = "projects"

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String(255), nullable=False, unique=True)
    tracker_token: str = Column(Text, nullable=False)
    tracker_org_id: str = Column(Text, nullable=True)
    gitlab_token: str = Column(Text, nullable=False)
    gitlab_webhook_secret: str = Column(Text, nullable=True)
    gitlab_project_id: int = Column(Integer, nullable=True)

    rules = relationship(
        "AutomationRule",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} name={self.name!r}>"
