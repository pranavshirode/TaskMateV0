import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TaskPriority, TaskStatus
from app.models.task_label import task_label_associations


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    client_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus), default=TaskStatus.BACKLOG, nullable=False, index=True
    )
    priority: Mapped[TaskPriority] = mapped_column(
        SAEnum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False, index=True
    )

    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tasks")
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    client: Mapped["Client"] = relationship("Client")
    labels: Mapped[list["TaskLabel"]] = relationship("TaskLabel", secondary=task_label_associations, lazy="select")
    events: Mapped[list["TaskEvent"]] = relationship("TaskEvent", back_populates="task", lazy="select")
