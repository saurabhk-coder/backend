import logging
import threading
from sqlalchemy import text
from app.auth_service.db.session import engine

logger = logging.getLogger(__name__)

CREATE_EMPLOYEE_DOCUMENTS_TABLE_SQL = """
CREATE SCHEMA IF NOT EXISTS hrms;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS hrms.employee_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id BIGINT NOT NULL REFERENCES hrms.employees(id) ON DELETE CASCADE,
    organization_id UUID,
    file_name VARCHAR(255) NOT NULL,
    file_title VARCHAR(255),
    file_category VARCHAR(50) NOT NULL DEFAULT 'document',
    content_type VARCHAR(100),
    file_size BIGINT,
    file_extension VARCHAR(20),
    gcs_bucket VARCHAR(100) NOT NULL DEFAULT 'hrms-aaralia',
    gcs_blob_name VARCHAR(500) NOT NULL,
    file_url TEXT,
    uploaded_by UUID,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_employee_documents_employee_id ON hrms.employee_documents (employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_documents_org_id ON hrms.employee_documents (organization_id);
CREATE INDEX IF NOT EXISTS idx_employee_documents_category ON hrms.employee_documents (file_category);
CREATE INDEX IF NOT EXISTS idx_employee_documents_blob_name ON hrms.employee_documents (gcs_blob_name);
"""


def _run_init():
    try:
        with engine.begin() as conn:
            conn.execute(text(CREATE_EMPLOYEE_DOCUMENTS_TABLE_SQL))
        logger.info("Employee documents database table initialized successfully.")
    except Exception as e:
        logger.warning(f"Could not automatically initialize Employee Documents table: {e}")


def init_documents_db():
    t = threading.Thread(target=_run_init, daemon=True)
    t.start()
