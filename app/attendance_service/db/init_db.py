import logging
import threading
from sqlalchemy import text
from app.auth_service.db.session import engine

logger = logging.getLogger(__name__)

CREATE_ATTENDANCE_TABLES_SQL = """
CREATE SCHEMA IF NOT EXISTS hrms;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS hrms.attendance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES hrms.organizations(id) ON DELETE CASCADE,
    employee_id BIGINT NOT NULL REFERENCES hrms.employees(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    shift_id UUID REFERENCES hrms.shifts(id) ON DELETE SET NULL,
    check_in TIMESTAMPTZ,
    check_out TIMESTAMPTZ,
    total_work_minutes INTEGER NOT NULL DEFAULT 0,
    break_minutes INTEGER NOT NULL DEFAULT 0,
    production_hours NUMERIC(5, 2) NOT NULL DEFAULT 0.0,
    overtime_hours NUMERIC(5, 2) NOT NULL DEFAULT 0.0,
    late_minutes INTEGER NOT NULL DEFAULT 0,
    early_leave_minutes INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(30) NOT NULL DEFAULT 'Absent',
    auto_checked_out BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_attendance_employee_date UNIQUE (employee_id, date)
);

CREATE INDEX IF NOT EXISTS idx_attendance_records_org_date ON hrms.attendance_records (organization_id, date);
CREATE INDEX IF NOT EXISTS idx_attendance_records_emp_date ON hrms.attendance_records (employee_id, date);

CREATE TABLE IF NOT EXISTS hrms.attendance_punches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES hrms.organizations(id) ON DELETE CASCADE,
    attendance_record_id UUID REFERENCES hrms.attendance_records(id) ON DELETE CASCADE,
    employee_id BIGINT NOT NULL REFERENCES hrms.employees(id) ON DELETE CASCADE,
    punch_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    punch_type VARCHAR(10) NOT NULL,
    location VARCHAR(255),
    device_info VARCHAR(255),
    ip_address VARCHAR(45),
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attendance_punches_record_id ON hrms.attendance_punches (attendance_record_id);
CREATE INDEX IF NOT EXISTS idx_attendance_punches_emp_time ON hrms.attendance_punches (employee_id, punch_time);

CREATE TABLE IF NOT EXISTS hrms.attendance_monthly_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES hrms.organizations(id) ON DELETE CASCADE,
    employee_id BIGINT NOT NULL REFERENCES hrms.employees(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    present_days INTEGER NOT NULL DEFAULT 0,
    absent_days INTEGER NOT NULL DEFAULT 0,
    half_days INTEGER NOT NULL DEFAULT 0,
    late_days INTEGER NOT NULL DEFAULT 0,
    total_production_hours NUMERIC(7, 2) NOT NULL DEFAULT 0.0,
    total_overtime_hours NUMERIC(7, 2) NOT NULL DEFAULT 0.0,
    working_days INTEGER NOT NULL DEFAULT 0,
    holidays INTEGER NOT NULL DEFAULT 0,
    leave_days INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_attendance_monthly_employee UNIQUE (employee_id, year, month)
);

CREATE INDEX IF NOT EXISTS idx_attendance_monthly_stats_org_ym ON hrms.attendance_monthly_stats (organization_id, year, month);

CREATE TABLE IF NOT EXISTS hrms.attendance_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES hrms.organizations(id) ON DELETE CASCADE,
    attendance_record_id UUID REFERENCES hrms.attendance_records(id) ON DELETE CASCADE,
    employee_id BIGINT NOT NULL,
    action VARCHAR(50) NOT NULL,
    old_values JSONB NOT NULL DEFAULT '{}'::jsonb,
    new_values JSONB NOT NULL DEFAULT '{}'::jsonb,
    reason TEXT,
    changed_by VARCHAR(100) NOT NULL DEFAULT 'system',
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attendance_audit_log_record ON hrms.attendance_audit_log (attendance_record_id);
CREATE INDEX IF NOT EXISTS idx_attendance_audit_log_org ON hrms.attendance_audit_log (organization_id);
"""


def _run_init():
    try:
        with engine.begin() as conn:
            conn.execute(text(CREATE_ATTENDANCE_TABLES_SQL))
        logger.info("Attendance database tables initialized successfully.")
    except Exception as e:
        logger.warning(f"Could not automatically initialize Attendance tables: {e}")


def init_attendance_db():
    t = threading.Thread(target=_run_init, daemon=True)
    t.start()
