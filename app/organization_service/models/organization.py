import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, DefaultClause, String, Text, Uuid, func, text
from ..db.base_class import Base


class OrganizationDb(Base):
    __tablename__ = "organizations"
    __table_args__ = {"schema": "hrms", "extend_existing": True}

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=DefaultClause(text("gen_random_uuid()")),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=True, index=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    status = Column(
        String(30),
        nullable=False,
        default="active",
        server_default=text("'active'"),
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
