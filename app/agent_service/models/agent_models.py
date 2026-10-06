import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    DefaultClause,
    ForeignKey,
    String,
    Text,
    Time,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.employee_service.db.base_class import Base


class AiAgentSessionDb(Base):
    __tablename__ = "ai_agent_sessions"
    __table_args__ = {"schema": "hrms", "extend_existing": True}

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=DefaultClause(text("gen_random_uuid()")),
        nullable=False,
    )
    session_name = Column(String(255), default="AI Agent Session", nullable=False)
    visitor_id = Column(String(100), nullable=True)
    metadata_json = Column(
        JSONB,
        default=dict,
        server_default=DefaultClause(text("'{}'::jsonb")),
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)
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

    messages = relationship(
        "AiAgentMessageDb",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="AiAgentMessageDb.created_at",
    )


class AiAgentMessageDb(Base):
    __tablename__ = "ai_agent_messages"
    __table_args__ = {"schema": "hrms", "extend_existing": True}

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=DefaultClause(text("gen_random_uuid()")),
        nullable=False,
    )
    session_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("hrms.ai_agent_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_type = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    action_type = Column(String(50), nullable=True, default="chat")
    metadata_json = Column(
        JSONB,
        default=dict,
        server_default=DefaultClause(text("'{}'::jsonb")),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    session = relationship("AiAgentSessionDb", back_populates="messages")


class AiAgentMeetingBookingDb(Base):
    __tablename__ = "ai_agent_meeting_bookings"
    __table_args__ = {"schema": "hrms", "extend_existing": True}

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=DefaultClause(text("gen_random_uuid()")),
        nullable=False,
    )
    session_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("hrms.ai_agent_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    preferred_date = Column(Date, nullable=False)
    preferred_time = Column(String(50), nullable=False)
    topic = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="pending")  # pending, confirmed, cancelled
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )


class AiAgentSupportRequestDb(Base):
    __tablename__ = "ai_agent_support_requests"
    __table_args__ = {"schema": "hrms", "extend_existing": True}

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=DefaultClause(text("gen_random_uuid()")),
        nullable=False,
    )
    session_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("hrms.ai_agent_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, default="medium")  # low, medium, high, urgent
    status = Column(String(30), nullable=False, default="open")  # open, in_progress, resolved
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )


class AiAgentConfigDb(Base):
    __tablename__ = "ai_agent_configs"
    __table_args__ = {"schema": "hrms", "extend_existing": True}

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=DefaultClause(text("gen_random_uuid()")),
        nullable=False,
    )
    agent_name = Column(String(100), nullable=False, default="Leslie")
    agent_title = Column(String(150), nullable=False, default="AI Product & Support Specialist")
    company_name = Column(String(100), nullable=False, default="Aaralia / Asana")
    avatar_url = Column(Text, nullable=True)
    video_url = Column(Text, nullable=True)
    greeting_message = Column(
        Text,
        nullable=False,
        default="Hi! I'm Leslie. How are you currently managing team goals and daily tasks? I can help show how our platform connects strategy to execution smoothly.",
    )
    suggested_questions = Column(
        JSONB,
        default=list,
        server_default=DefaultClause(
            text(
                '\'["What are our shift timings?", "Who is available in the engineering department?", "What skills does our team have?", "What is our weekend and calendar policy?"]\'::jsonb'
            )
        ),
        nullable=False,
    )
    quick_actions = Column(
        JSONB,
        default=list,
        server_default=DefaultClause(
            text(
                '\'[{"id": "book_meeting", "title": "Book a Meeting", "action": "open_modal"}, {"id": "request_support", "title": "Request Support", "action": "open_modal"}]\'::jsonb'
            )
        ),
        nullable=False,
    )
    system_prompt = Column(
        Text,
        nullable=True,
        default="You are Leslie, an intelligent AI concierge for Aaralia HRMS. You answer user queries accurately by retrieving real data from the database.",
    )
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
