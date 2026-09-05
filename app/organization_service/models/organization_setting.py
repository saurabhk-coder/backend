import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    DateTime,
    DefaultClause,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from ..db.base_class import Base


class OrganizationSettingDb(Base):
    __tablename__ = "organization_settings"
    __table_args__ = (
        UniqueConstraint("organization_id", "setting_key", name="uq_organization_setting"),
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
    setting_key = Column(String(255), nullable=False, index=True)
    setting_value = Column(Text, nullable=True)
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
