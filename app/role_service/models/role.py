import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, DefaultClause, text, func, JSON, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from ..db.base_class import Base


class RoleDb(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "hrms", "extend_existing": True}

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=DefaultClause(text("gen_random_uuid()")),
        nullable=False,
    )
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    permissions_json = Column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
        default=dict,
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
