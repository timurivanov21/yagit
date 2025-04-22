from sqlalchemy import Column, DateTime, func


class TimestampMixin:
    """Adds `created_at` and `updated_at` columns to inheriting model."""

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
