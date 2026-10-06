import logging
from sqlalchemy import text
from app.auth_service.db.session import engine

logger = logging.getLogger(__name__)

CREATE_AGENT_TABLES_SQL = """
CREATE SCHEMA IF NOT EXISTS hrms;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS hrms.ai_agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_name VARCHAR(255) NOT NULL DEFAULT 'AI Agent Session',
    visitor_id VARCHAR(100),
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hrms.ai_agent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES hrms.ai_agent_sessions(id) ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    action_type VARCHAR(50) DEFAULT 'chat',
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hrms.ai_agent_meeting_bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES hrms.ai_agent_sessions(id) ON DELETE SET NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    preferred_date DATE NOT NULL,
    preferred_time VARCHAR(50) NOT NULL,
    topic TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hrms.ai_agent_support_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES hrms.ai_agent_sessions(id) ON DELETE SET NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    status VARCHAR(30) NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hrms.ai_agent_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name VARCHAR(100) NOT NULL DEFAULT 'Leslie',
    agent_title VARCHAR(150) NOT NULL DEFAULT 'AI Product & Support Specialist',
    company_name VARCHAR(100) NOT NULL DEFAULT 'Aaralia',
    avatar_url TEXT,
    video_url TEXT,
    greeting_message TEXT NOT NULL DEFAULT 'Hi! I''m Leslie. How are you currently managing team goals and daily tasks? I can help show how our platform connects strategy to execution smoothly.',
    suggested_questions JSONB NOT NULL DEFAULT '["What are our shift timings?", "Who is available in the engineering department?", "What skills does our team have?", "What is our weekend and calendar policy?"]'::jsonb,
    quick_actions JSONB NOT NULL DEFAULT '[{"id": "book_meeting", "title": "Book a Meeting", "action": "open_modal"}, {"id": "request_support", "title": "Request Support", "action": "open_modal"}]'::jsonb,
    system_prompt TEXT DEFAULT 'You are Leslie, an intelligent AI concierge for Aaralia HRMS. You answer user queries accurately by retrieving real data from the database.',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


import threading

def _run_init():
    try:
        with engine.begin() as conn:
            conn.execute(text(CREATE_AGENT_TABLES_SQL))
        logger.info("AI Agent database tables initialized successfully.")
    except Exception as e:
        logger.warning(f"Could not automatically initialize AI Agent tables (database may be offline or unreachable): {e}")

def init_agent_db():
    t = threading.Thread(target=_run_init, daemon=True)
    t.start()
