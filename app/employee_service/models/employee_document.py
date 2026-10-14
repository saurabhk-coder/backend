import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    DefaultClause,
    ForeignKey,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import relationship
from ..db.base_class import Base


class EmployeeDocumentDb(Base):
    __tablename__ = "employee_documents"
    __table_args__ = {"schema": "hrms", "extend_existing": True}

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=DefaultClause(text("gen_random_uuid()")),
        nullable=False,
    )
    employee_id = Column(
        BigInteger,
        ForeignKey("hrms.employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id = Column(
        Uuid(as_uuid=True),
        nullable=True,
        index=True,
    )
    file_name = Column(String(255), nullable=False)
    file_title = Column(String(255), nullable=True)
    file_category = Column(
        String(50),
        nullable=False,
        default="document",
        server_default=text("'document'"),
        index=True,
    )  # govt_id_proof, profile_photo, resume, contract, certificate, tax_document, other
    content_type = Column(String(100), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    file_extension = Column(String(20), nullable=True)
    gcs_bucket = Column(
        String(100),
        nullable=False,
        default="hrms-aaralia",
        server_default=text("'hrms-aaralia'"),
    )
    gcs_blob_name = Column(String(500), nullable=False, index=True)
    file_url = Column(Text, nullable=True)
    uploaded_by = Column(Uuid(as_uuid=True), nullable=True)
    description = Column(Text, nullable=True)
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

    employee = relationship("EmployeeDb", backref="documents", foreign_keys=[employee_id])
