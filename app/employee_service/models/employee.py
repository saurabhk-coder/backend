from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, String, func
from ..db.base_class import Base


class EmployeeDb(Base):
    __tablename__ = "employees"
    __table_args__ = {"schema": "hrms", "extend_existing": True}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    employee_code = Column(String(50), nullable=True, unique=True, index=True)
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
