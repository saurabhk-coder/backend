import uuid
from datetime import datetime, time, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    DefaultClause,
    ForeignKey,
    JSON,
    String,
    Time,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from ..db.base_class import Base


class CalendarSettingDb(Base):
    __tablename__ = "calendar_settings"
    __table_args__ = (
        UniqueConstraint("organization_id", "location", name="uq_calendar_setting_org_location"),
        {"schema": "hrms", "extend_existing": True},
    )

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=DefaultClause(text("gen_random_uuid()")),
        nullable=False,
    )
    organization_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("hrms.organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    location = Column(String(255), nullable=False)
    is_default = Column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False,
    )
    fiscal_year_same_as_calendar = Column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
    )
    fiscal_year_start_month = Column(
        String(20),
        default="January",
        server_default=text("'January'"),
        nullable=False,
    )
    fiscal_year_end_month = Column(
        String(20),
        default="December",
        server_default=text("'December'"),
        nullable=False,
    )
    leave_year_same_as_calendar = Column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
    )
    leave_year_start_month = Column(
        String(20),
        default="January",
        server_default=text("'January'"),
        nullable=False,
    )
    leave_year_end_month = Column(
        String(20),
        default="December",
        server_default=text("'December'"),
        nullable=False,
    )
    max_working_hours_per_day = Column(
        String(10),
        default="09:00",
        server_default=text("'09:00'"),
        nullable=True,
    )
    week_starts_on = Column(
        String(15),
        default="Monday",
        server_default=text("'Monday'"),
        nullable=False,
    )
    shift_start_time = Column(
        Time,
        default=time(9, 0),
        server_default=text("'09:00:00'"),
        nullable=True,
    )
    shift_end_time = Column(
        Time,
        default=time(18, 0),
        server_default=text("'18:00:00'"),
        nullable=True,
    )
    full_day_hours = Column(
        String(10),
        default="08:00",
        server_default=text("'08:00'"),
        nullable=False,
    )
    full_day_tolerance = Column(
        String(10),
        default="00:00",
        server_default=text("'00:00'"),
        nullable=True,
    )
    half_day_hours = Column(
        String(10),
        default="04:00",
        server_default=text("'04:00'"),
        nullable=False,
    )
    half_day_tolerance = Column(
        String(10),
        default="00:00",
        server_default=text("'00:00'"),
        nullable=True,
    )
    weekend_definition = Column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        server_default=text("'{}'"),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    weekend_rules = relationship(
        "CalendarWeekendRuleDb",
        back_populates="calendar_setting",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CalendarWeekendRuleDb(Base):
    __tablename__ = "calendar_weekend_rules"
    __table_args__ = (
        UniqueConstraint("calendar_setting_id", "day_of_week", name="uq_calendar_weekend_rule_setting_day"),
        {"schema": "hrms", "extend_existing": True},
    )

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=DefaultClause(text("gen_random_uuid()")),
        nullable=False,
    )
    calendar_setting_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("hrms.calendar_settings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_of_week = Column(String(15), nullable=False)
    week_1st = Column(Boolean, default=False, server_default=text("false"), nullable=False)
    week_2nd = Column(Boolean, default=False, server_default=text("false"), nullable=False)
    week_3rd = Column(Boolean, default=False, server_default=text("false"), nullable=False)
    week_4th = Column(Boolean, default=False, server_default=text("false"), nullable=False)
    week_5th = Column(Boolean, default=False, server_default=text("false"), nullable=False)
    week_last = Column(Boolean, default=False, server_default=text("false"), nullable=False)
    week_alt = Column(Boolean, default=False, server_default=text("false"), nullable=False)

    calendar_setting = relationship("CalendarSettingDb", back_populates="weekend_rules")
