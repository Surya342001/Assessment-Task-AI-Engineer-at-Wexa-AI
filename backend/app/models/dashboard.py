
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class WidgetType(str, enum.Enum):
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    KPI_CARD = "kpi_card"
    TABLE = "table"


class Dashboard(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dashboards"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    layout: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    public_slug: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    refresh_interval: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Refresh interval in seconds (30, 60, 300)"
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship()  # type: ignore[name-defined]
    created_by: Mapped["User | None"] = relationship(foreign_keys=[created_by_id])  # type: ignore[name-defined]
    widgets: Mapped[list["Widget"]] = relationship(
        back_populates="dashboard", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Dashboard id={self.id} name={self.name}>"


class Widget(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "widgets"

    dashboard_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dashboards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    widget_type: Mapped[WidgetType] = mapped_column(Enum(WidgetType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    query_config: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict,
        comment="Stores event_name, filters, aggregation, time_range, group_by"
    )
    position: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict,
        comment="Grid position: {x, y, w, h}"
    )
    options: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Relationships
    dashboard: Mapped["Dashboard"] = relationship(back_populates="widgets")

    def __repr__(self) -> str:
        return f"<Widget id={self.id} type={self.widget_type} dashboard={self.dashboard_id}>"
