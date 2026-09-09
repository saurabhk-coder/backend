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
    __tablename__ = "employee_department_information"
    __table_args__ = {"schema": "hrms", "extend_existing": True}

    employee_id = Column(
        BigInteger,
        ForeignKey("hrms.employees.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    department = Column(String(150), nullable=True)
    designation = Column(String(150), nullable=True)
    reporting_manager_id = Column(
        BigInteger,
        ForeignKey("hrms.employees.id", ondelete="SET NULL"),
        nullable=True,
    )
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

    employee = relationship("EmployeeDb", backref="department_information", foreign_keys=[employee_id])
    reporting_manager = relationship("EmployeeDb", foreign_keys=[reporting_manager_id])
