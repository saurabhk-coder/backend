import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    DefaultClause,
    ForeignKey,
    Integer,
    JSON,
    String,
    Time,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from ..db.base_class import Base


class ShiftDb(Base):
    __tablename__ = "shifts"
    __table_args__ = {"schema": "hrms", "extend_existing": True}

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
    name = Column(String(255), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    shift_duration = Column(String(10), nullable=False, default="09:00")
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    people_required = Column(String(50), nullable=True)
    color = Column(
        String(32),
        default="#F05A28",
        server_default=text("'#F05A28'"),
        nullable=False,
    )
    work_area = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    pay_calculation_type = Column(
        String(20),
        nullable=False,
        default="per_day",
        server_default=text("'per_day'"),
    )
    full_day_hours = Column(
        String(10),
        nullable=False,
        default="08:00",
        server_default=text("'08:00'"),
    )
    full_day_tolerance = Column(
        String(10),
        default="00:00",
        server_default=text("'00:00'"),
        nullable=True,
    )
    half_day_hours = Column(
        String(10),
        nullable=False,
        default="04:00",
        server_default=text("'04:00'"),
    )
    half_day_tolerance = Column(
        String(10),
        default="00:00",
        server_default=text("'00:00'"),
        nullable=True,
    )
    recurrence_pattern = Column(
        String(20),
        nullable=False,
        default="daily",
        server_default=text("'daily'"),
    )
    weekly_working_days = Column(
        JSON().with_variant(JSONB, "postgresql"),
        default=lambda: ["Mon", "Tue", "Wed", "Thu", "Fri"],
        nullable=False,
    )
    calendar_weekend_policy = Column(
        String(20),
        nullable=False,
        default="calendar",
        server_default=text("'calendar'"),
    )
    is_active = Column(
        Boolean,
        default=True,
        server_default=text("true"),
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

    grace_period = relationship(
        "ShiftGracePeriodDb",
        back_populates="shift",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reminder = relationship(
        "ShiftReminderDb",
        back_populates="shift",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ShiftGracePeriodDb(Base):
    __tablename__ = "shift_grace_periods"
    __table_args__ = {"schema": "hrms", "extend_existing": True}

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=DefaultClause(text("gen_random_uuid()")),
        nullable=False,
    )
    shift_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("hrms.shifts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    is_enabled = Column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False,
    )
    late_check_in_minutes = Column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
    )
    early_check_out_minutes = Column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
    )

    shift = relationship("ShiftDb", back_populates="grace_period")


class ShiftReminderDb(Base):
    __tablename__ = "shift_reminders"
    __table_args__ = {"schema": "hrms", "extend_existing": True}

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=DefaultClause(text("gen_random_uuid()")),
        nullable=False,
    )
    shift_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("hrms.shifts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    check_in_enabled = Column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False,
    )
    check_in_before = Column(
        String(10),
        default="00:00",
        server_default=text("'00:00'"),
        nullable=True,
    )
    check_in_after = Column(
        String(10),
        default="00:00",
        server_default=text("'00:00'"),
        nullable=True,
    )
    check_out_enabled = Column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False,
    )
    check_out_before = Column(
        String(10),
        default="00:00",
        server_default=text("'00:00'"),
        nullable=True,
    )
    check_out_after = Column(
        String(10),
        default="00:00",
        server_default=text("'00:00'"),
        nullable=True,
    )

    shift = relationship("ShiftDb", back_populates="reminder")
