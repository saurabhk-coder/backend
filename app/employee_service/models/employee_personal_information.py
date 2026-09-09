from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship
from ..db.base_class import Base


class EmployeePersonalInformationDb(Base):
    __tablename__ = "employee_personal_information"
    __table_args__ = {"schema": "hrms", "extend_existing": True}

    employee_id = Column(
        BigInteger,
        ForeignKey("hrms.employees.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    profile_photo = Column(Text, nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    mobile_number = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    father_name = Column(String(150), nullable=True)
    mother_name = Column(String(150), nullable=True)
    marital_status = Column(String(30), nullable=True)
    spouse_name = Column(String(150), nullable=True)
    emergency_contact = Column(String(20), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    govt_id_proof = Column(String(50), nullable=True)
    id_proof_number = Column(String(100), nullable=True)
    gender = Column(String(30), nullable=True)
    nationality = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
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

    employee = relationship("EmployeeDb", backref="personal_information", foreign_keys=[employee_id])
