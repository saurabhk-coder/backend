from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship
from ..db.base_class import Base


class EmployeeProfessionalInformationDb(Base):
    __tablename__ = "employee_professional_information"
    __table_args__ = {"schema": "hrms", "extend_existing": True}

    employee_id = Column(
        BigInteger,
        ForeignKey("hrms.employees.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    tenth_roll = Column(String(100), nullable=True)
    tenth_percentage_cgpa = Column(String(20), nullable=True)
    twelfth_roll = Column(String(100), nullable=True)
    twelfth_percentage_cgpa = Column(String(20), nullable=True)
    graduation_roll = Column(String(100), nullable=True)
    graduation_percentage_cgpa = Column(String(20), nullable=True)
    post_graduation_roll = Column(String(100), nullable=True)
    post_graduation_percentage_cgpa = Column(String(20), nullable=True)
    total_experience_years = Column(String(100), nullable=True)
    last_company_details = Column(String(255), nullable=True)
    last_ctc = Column(Numeric(15, 2), nullable=True)
    certifications = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)

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

    employee = relationship("EmployeeDb", backref="professional_information", foreign_keys=[employee_id])
