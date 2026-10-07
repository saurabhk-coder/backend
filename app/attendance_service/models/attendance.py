import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    DefaultClause,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from ..db.base_class import Base


class AttendanceRecordDb(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("employee_id", "date", name="uq_attendance_employee_date"),
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
    employee_id = Column(
        BigInteger,
        ForeignKey("hrms.employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date = Column(Date, nullable=False, index=True)
    shift_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("hrms.shifts.id", ondelete="SET NULL"),
        nullable=True,
    )
    check_in = Column(DateTime(timezone=True), nullable=True)
    check_out = Column(DateTime(timezone=True), nullable=True)
    total_work_minutes = Column(Integer, nullable=False, default=0, server_default=text("0"))
    break_minutes = Column(Integer, nullable=False, default=0, server_default=text("0"))
    production_hours = Column(
        Numeric(5, 2),
        nullable=False,
        default=0.0,
        server_default=text("0.0"),
    )
    overtime_hours = Column(
        Numeric(5, 2),
        nullable=False,
        default=0.0,
        server_default=text("0.0"),
    )
    late_minutes = Column(Integer, nullable=False, default=0, server_default=text("0"))
    early_leave_minutes = Column(Integer, nullable=False, default=0, server_default=text("0"))
    status = Column(
        String(30),
        nullable=False,
        default="Absent",
        server_default=text("'Absent'"),
    )
    auto_checked_out = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    notes = Column(Text, nullable=True)
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

    punches = relationship(
        "AttendancePunchDb",
        back_populates="attendance_record",
        cascade="all, delete-orphan",
        order_by="AttendancePunchDb.punch_time",
    )


class AttendancePunchDb(Base):
    __tablename__ = "attendance_punches"
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
    attendance_record_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("hrms.attendance_records.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    employee_id = Column(
        BigInteger,
        ForeignKey("hrms.employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    punch_time = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    punch_type = Column(String(10), nullable=False)  # IN / OUT
    location = Column(String(255), nullable=True)
    device_info = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    attendance_record = relationship("AttendanceRecordDb", back_populates="punches")


class AttendanceMonthlyStatsDb(Base):
    __tablename__ = "attendance_monthly_stats"
    __table_args__ = (
        UniqueConstraint("employee_id", "year", "month", name="uq_attendance_monthly_employee"),
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
    employee_id = Column(
        BigInteger,
        ForeignKey("hrms.employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    present_days = Column(Integer, nullable=False, default=0, server_default=text("0"))
    absent_days = Column(Integer, nullable=False, default=0, server_default=text("0"))
    half_days = Column(Integer, nullable=False, default=0, server_default=text("0"))
    late_days = Column(Integer, nullable=False, default=0, server_default=text("0"))
    total_production_hours = Column(
        Numeric(7, 2),
        nullable=False,
        default=0.0,
        server_default=text("0.0"),
    )
    total_overtime_hours = Column(
        Numeric(7, 2),
        nullable=False,
        default=0.0,
        server_default=text("0.0"),
    )
    working_days = Column(Integer, nullable=False, default=0, server_default=text("0"))
    holidays = Column(Integer, nullable=False, default=0, server_default=text("0"))
    leave_days = Column(Integer, nullable=False, default=0, server_default=text("0"))
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


class AttendanceAuditLogDb(Base):
    __tablename__ = "attendance_audit_log"
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
    attendance_record_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("hrms.attendance_records.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    employee_id = Column(BigInteger, nullable=False, index=True)
    action = Column(String(50), nullable=False)
    old_values = Column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
        server_default=text("'{}'"),
    )
    new_values = Column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
        server_default=text("'{}'"),
    )
    reason = Column(Text, nullable=True)
    changed_by = Column(
        String(100),
        nullable=False,
        default="system",
        server_default=text("'system'"),
    )
    changed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
