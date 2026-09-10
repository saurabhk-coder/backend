from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import relationship
from ..db.base_class import Base


class EmployeeDepartmentInformationDb(Base):
    __tablename__ = "departments"
    __table_args__ = {"schema": "hrms", "extend_existing": True}

    employee_id = Column(
        BigInteger,
        primary_key=True,
        nullable=False,
    )
    department = Column(String(150), nullable=True)
    designation = Column(String(150), nullable=True)
    reporting_manager_id =Column(String(50), nullable=True)
    work_location = Column(String(150), nullable=True)
    work_mode = Column(String(50), nullable=True)
    employment_type = Column(String(50), nullable=True)
    ctc_offered = Column(Numeric(15, 2), nullable=True)

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

    employee = Column(String(50), nullable=True)
    reporting_manager = Column(String(50), nullable=True)
