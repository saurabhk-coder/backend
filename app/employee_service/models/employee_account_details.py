from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import relationship
from ..db.base_class import Base


class EmployeeAccountDetailsDb(Base):
    __tablename__ = "employee_account_details"
    __table_args__ = {"schema": "hrms", "extend_existing": True}

    employee_id = Column(
        BigInteger,
        ForeignKey("hrms.employees.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    bank_name = Column(String(150), nullable=True)
    ifsc_code = Column(String(20), nullable=True)
    account_number = Column(String(50), nullable=True)
    branch_name = Column(String(50), nullable=True)

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

    employee = relationship("EmployeeDb", backref="account_details", foreign_keys=[employee_id])
