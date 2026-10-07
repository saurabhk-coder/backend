-- ============================================================================
-- Complete Database Schema Script for Aaralia Backend (PostgreSQL)
-- All tables in foreign-key dependency order
-- Can be executed directly in pgAdmin / psql / DBeaver
-- ============================================================================

-- 1. Ensure Schema and UUID Extension Exist
CREATE SCHEMA IF NOT EXISTS hrms;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- 1. hrms.organizations (Multi-Tenant Organization Anchor)
-- ============================================================================
CREATE TABLE IF NOT EXISTS hrms.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_organizations_slug ON hrms.organizations (slug);

-- ============================================================================
-- 2. hrms.roles (RBAC System Roles)
-- ============================================================================
CREATE TABLE IF NOT EXISTS hrms.roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    permissions_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_roles_name ON hrms.roles (name);

-- ============================================================================
-- 3. hrms.users (User Accounts)
-- ============================================================================
CREATE TABLE IF NOT EXISTS hrms.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES hrms.organizations(id) ON DELETE SET NULL,
    role_id UUID REFERENCES hrms.roles(id) ON DELETE SET NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_salt VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    country_code VARCHAR(10),
    status VARCHAR(50),
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_org_id ON hrms.users (organization_id);
CREATE INDEX IF NOT EXISTS idx_users_role_id ON hrms.users (role_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON hrms.users (email);

-- ============================================================================
-- 4. hrms.organization_settings (Generic Key-Value Organization Configuration)
-- ============================================================================
CREATE TABLE IF NOT EXISTS hrms.organization_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES hrms.organizations(id) ON DELETE CASCADE,
    setting_key VARCHAR(255) NOT NULL,
    setting_value TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_organization_setting UNIQUE (organization_id, setting_key)
);

CREATE INDEX IF NOT EXISTS idx_org_settings_org_id ON hrms.organization_settings (organization_id);
CREATE INDEX IF NOT EXISTS idx_org_settings_key ON hrms.organization_settings (setting_key);

-- ============================================================================
-- 5. hrms.calendar_settings (Primary Calendar Settings Table)
-- ============================================================================
CREATE TABLE IF NOT EXISTS hrms.calendar_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES hrms.organizations(id) ON DELETE CASCADE,
    location VARCHAR(255) NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    fiscal_year_same_as_calendar BOOLEAN NOT NULL DEFAULT TRUE,
    fiscal_year_start_month VARCHAR(20) NOT NULL DEFAULT 'January',
    fiscal_year_end_month VARCHAR(20) NOT NULL DEFAULT 'December',
    leave_year_same_as_calendar BOOLEAN NOT NULL DEFAULT TRUE,
    leave_year_start_month VARCHAR(20) NOT NULL DEFAULT 'January',
    leave_year_end_month VARCHAR(20) NOT NULL DEFAULT 'December',
    max_working_hours_per_day VARCHAR(10) DEFAULT '09:00',
    week_starts_on VARCHAR(15) NOT NULL DEFAULT 'Monday',
    shift_start_time TIME DEFAULT '09:00:00',
    shift_end_time TIME DEFAULT '18:00:00',
    full_day_hours VARCHAR(10) NOT NULL DEFAULT '08:00',
    full_day_tolerance VARCHAR(10) DEFAULT '00:00',
    half_day_hours VARCHAR(10) NOT NULL DEFAULT '04:00',
    half_day_tolerance VARCHAR(10) DEFAULT '00:00',
    weekend_definition JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_calendar_settings_org_location UNIQUE (organization_id, location)
);

CREATE INDEX IF NOT EXISTS idx_calendar_settings_org_id ON hrms.calendar_settings (organization_id);
CREATE INDEX IF NOT EXISTS idx_calendar_settings_is_default ON hrms.calendar_settings (organization_id, is_default);
CREATE INDEX IF NOT EXISTS idx_calendar_settings_location ON hrms.calendar_settings (organization_id, location);
CREATE INDEX IF NOT EXISTS idx_calendar_settings_weekend_def ON hrms.calendar_settings USING GIN (weekend_definition);

-- ============================================================================
-- 6. hrms.calendar_weekend_rules (Normalized 7-Day Occurrence Rules Table)
-- ============================================================================
CREATE TABLE IF NOT EXISTS hrms.calendar_weekend_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    calendar_setting_id UUID NOT NULL REFERENCES hrms.calendar_settings(id) ON DELETE CASCADE,
    day_of_week VARCHAR(15) NOT NULL,
    week_1st BOOLEAN NOT NULL DEFAULT FALSE,
    week_2nd BOOLEAN NOT NULL DEFAULT FALSE,
    week_3rd BOOLEAN NOT NULL DEFAULT FALSE,
    week_4th BOOLEAN NOT NULL DEFAULT FALSE,
    week_5th BOOLEAN NOT NULL DEFAULT FALSE,
    week_last BOOLEAN NOT NULL DEFAULT FALSE,
    week_alt BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_calendar_weekend_rules_setting_day UNIQUE (calendar_setting_id, day_of_week)
);

CREATE INDEX IF NOT EXISTS idx_calendar_weekend_rules_setting_id ON hrms.calendar_weekend_rules (calendar_setting_id);

-- ============================================================================
-- 7. hrms.shifts (Shift Policy Configuration)
-- ============================================================================
CREATE TABLE IF NOT EXISTS hrms.shifts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES hrms.organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    shift_duration VARCHAR(10) NOT NULL DEFAULT '09:00',
    start_date DATE,
    end_date DATE,
    people_required VARCHAR(50),
    color VARCHAR(32) NOT NULL DEFAULT '#F05A28',
    work_area VARCHAR(255),
    department VARCHAR(255),
    location VARCHAR(255),
    pay_calculation_type VARCHAR(20) NOT NULL DEFAULT 'per_day',
    full_day_hours VARCHAR(10) NOT NULL DEFAULT '08:00',
    full_day_tolerance VARCHAR(10) DEFAULT '00:00',
    half_day_hours VARCHAR(10) NOT NULL DEFAULT '04:00',
    half_day_tolerance VARCHAR(10) DEFAULT '00:00',
    recurrence_pattern VARCHAR(20) NOT NULL DEFAULT 'daily',
    weekly_working_days JSONB NOT NULL DEFAULT '["Mon","Tue","Wed","Thu","Fri"]'::jsonb,
    calendar_weekend_policy VARCHAR(20) NOT NULL DEFAULT 'calendar',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_shifts_org_id ON hrms.shifts (organization_id);
CREATE INDEX IF NOT EXISTS idx_shifts_name ON hrms.shifts (name);
CREATE INDEX IF NOT EXISTS idx_shifts_department ON hrms.shifts (department);
CREATE INDEX IF NOT EXISTS idx_shifts_location ON hrms.shifts (location);
CREATE INDEX IF NOT EXISTS idx_shifts_is_active ON hrms.shifts (is_active);

-- ============================================================================
-- 8. hrms.shift_grace_periods (Shift Grace Period Settings)
-- ============================================================================
CREATE TABLE IF NOT EXISTS hrms.shift_grace_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shift_id UUID NOT NULL REFERENCES hrms.shifts(id) ON DELETE CASCADE UNIQUE,
    is_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    late_check_in_minutes INTEGER NOT NULL DEFAULT 0,
    early_check_out_minutes INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_shift_grace_periods_shift_id ON hrms.shift_grace_periods (shift_id);

-- ============================================================================
-- 9. hrms.shift_reminders (Shift Reminder Settings)
-- ============================================================================
CREATE TABLE IF NOT EXISTS hrms.shift_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shift_id UUID NOT NULL REFERENCES hrms.shifts(id) ON DELETE CASCADE UNIQUE,
    check_in_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    check_in_before VARCHAR(10) DEFAULT '00:00',
    check_in_after VARCHAR(10) DEFAULT '00:00',
    check_out_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    check_out_before VARCHAR(10) DEFAULT '00:00',
    check_out_after VARCHAR(10) DEFAULT '00:00'
);

CREATE INDEX IF NOT EXISTS idx_shift_reminders_shift_id ON hrms.shift_reminders (shift_id);

-- ============================================================================
-- 10. hrms.employees (Core Employee Record)
-- ============================================================================
CREATE TABLE IF NOT EXISTS hrms.employees (

    id BIGSERIAL PRIMARY KEY,
    employee_code VARCHAR(50) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_employees_code ON hrms.employees (employee_code);

-- ============================================================================
-- 8. hrms.departments (Employee Department & Job Information)
-- ============================================================================
CREATE TABLE IF NOT EXISTS hrms.departments (
    employee_id BIGINT PRIMARY KEY REFERENCES hrms.employees(id) ON DELETE CASCADE,
    department VARCHAR(150),
    designation VARCHAR(150),
    reporting_manager_id VARCHAR(50),
    work_location VARCHAR(150),
    work_mode VARCHAR(50),
    employment_type VARCHAR(50),
    ctc_offered NUMERIC(15, 2),
    employee VARCHAR(50),
    reporting_manager VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 9. hrms.employee_personal_information (Employee Personal Details)
-- ============================================================================
CREATE TABLE IF NOT EXISTS hrms.employee_personal_information (
    employee_id BIGINT PRIMARY KEY REFERENCES hrms.employees(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES hrms.organizations(id) ON DELETE CASCADE,
    profile_photo TEXT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    mobile_number VARCHAR(20),
    email VARCHAR(255),
    father_name VARCHAR(150),
    mother_name VARCHAR(150),
    marital_status VARCHAR(30),
    spouse_name VARCHAR(150),
    emergency_contact VARCHAR(20),
    date_of_birth DATE,
    govt_id_proof VARCHAR(50),
    id_proof_number VARCHAR(100),
    gender VARCHAR(30),
    nationality VARCHAR(100),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    zip_code VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_emp_personal_org_id ON hrms.employee_personal_information (organization_id);

-- ============================================================================
-- 10. hrms.employee_professional_information (Employee Education & Past Experience)
-- ============================================================================
CREATE TABLE IF NOT EXISTS hrms.employee_professional_information (
    employee_id BIGINT PRIMARY KEY REFERENCES hrms.employees(id) ON DELETE CASCADE,
    tenth_roll VARCHAR(100),
    tenth_percentage_cgpa VARCHAR(20),
    twelfth_roll VARCHAR(100),
    twelfth_percentage_cgpa VARCHAR(20),
    graduation_roll VARCHAR(100),
    graduation_percentage_cgpa VARCHAR(20),
    post_graduation_roll VARCHAR(100),
    post_graduation_percentage_cgpa VARCHAR(20),
    total_experience_years VARCHAR(100),
    last_company_details VARCHAR(255),
    last_ctc NUMERIC(15, 2),
    certifications TEXT,
    skills TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 11. hrms.employee_account_details (Employee Bank Account & Financial Details)
-- ============================================================================
CREATE TABLE IF NOT EXISTS hrms.employee_account_details (
    employee_id BIGINT PRIMARY KEY REFERENCES hrms.employees(id) ON DELETE CASCADE,
    bank_name VARCHAR(150),
    ifsc_code VARCHAR(20),
    account_number VARCHAR(50),
    branch_name VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 12. country / lst_country (Country Lookup)
-- ============================================================================
CREATE TABLE IF NOT EXISTS country (
    id SERIAL PRIMARY KEY,
    country_name VARCHAR(255) UNIQUE,
    country_code VARCHAR(10) UNIQUE
);

CREATE TABLE IF NOT EXISTS lst_country (
    id SERIAL PRIMARY KEY,
    country_name VARCHAR(255) UNIQUE,
    country_code VARCHAR(10) UNIQUE
);

-- ============================================================================
-- 13. accounts & file_folder (Auth & Document Storage)
-- ============================================================================
CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_name VARCHAR(255) UNIQUE,
    created_at VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS file_folder (
    folder_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    folder_name VARCHAR(255),
    file_id UUID,
    file_name VARCHAR(255),
    file_size VARCHAR(100),
    content_type VARCHAR(100),
    file_url TEXT,
    file_extension VARCHAR(50),
    storage_file_name VARCHAR(255),
    created_by UUID,
    updated_by VARCHAR(100),
    created_at VARCHAR(100),
    updated_at VARCHAR(100),
    account_id UUID,
    display_name VARCHAR(255)
);

-- ============================================================================
-- Trigger Function for Auto-Updating updated_at Timestamps
-- ============================================================================
CREATE OR REPLACE FUNCTION hrms.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_organizations_updated_at') THEN
        CREATE TRIGGER trg_organizations_updated_at
        BEFORE UPDATE ON hrms.organizations
        FOR EACH ROW EXECUTE FUNCTION hrms.update_timestamp();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_roles_updated_at') THEN
        CREATE TRIGGER trg_roles_updated_at
        BEFORE UPDATE ON hrms.roles
        FOR EACH ROW EXECUTE FUNCTION hrms.update_timestamp();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_calendar_settings_updated_at') THEN
        CREATE TRIGGER trg_calendar_settings_updated_at
        BEFORE UPDATE ON hrms.calendar_settings
        FOR EACH ROW EXECUTE FUNCTION hrms.update_timestamp();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_shifts_updated_at') THEN
        CREATE TRIGGER trg_shifts_updated_at
        BEFORE UPDATE ON hrms.shifts
        FOR EACH ROW EXECUTE FUNCTION hrms.update_timestamp();
    END IF;


    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_org_settings_updated_at') THEN
        CREATE TRIGGER trg_org_settings_updated_at
        BEFORE UPDATE ON hrms.organization_settings
        FOR EACH ROW EXECUTE FUNCTION hrms.update_timestamp();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_employees_updated_at') THEN
        CREATE TRIGGER trg_employees_updated_at
        BEFORE UPDATE ON hrms.employees
        FOR EACH ROW EXECUTE FUNCTION hrms.update_timestamp();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_departments_updated_at') THEN
        CREATE TRIGGER trg_departments_updated_at
        BEFORE UPDATE ON hrms.departments
        FOR EACH ROW EXECUTE FUNCTION hrms.update_timestamp();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_emp_personal_info_updated_at') THEN
        CREATE TRIGGER trg_emp_personal_info_updated_at
        BEFORE UPDATE ON hrms.employee_personal_information
        FOR EACH ROW EXECUTE FUNCTION hrms.update_timestamp();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_emp_prof_info_updated_at') THEN
        CREATE TRIGGER trg_emp_prof_info_updated_at
        BEFORE UPDATE ON hrms.employee_professional_information
        FOR EACH ROW EXECUTE FUNCTION hrms.update_timestamp();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_emp_acc_details_updated_at') THEN
        CREATE TRIGGER trg_emp_acc_details_updated_at
        BEFORE UPDATE ON hrms.employee_account_details
        FOR EACH ROW EXECUTE FUNCTION hrms.update_timestamp();
    END IF;
END $$;

-- ============================================================================
-- 14. hrms.ai_agent_sessions (Conversational Sessions for AI Agent)
-- ============================================================================
CREATE TABLE IF NOT EXISTS hrms.ai_agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_name VARCHAR(255) NOT NULL DEFAULT 'AI Agent Session',
    visitor_id VARCHAR(100),
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ai_agent_sessions_visitor_id ON hrms.ai_agent_sessions (visitor_id);

-- ============================================================================
-- 15. hrms.ai_agent_messages (Messages within AI Agent Sessions)
-- ============================================================================
CREATE TABLE IF NOT EXISTS hrms.ai_agent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES hrms.ai_agent_sessions(id) ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    action_type VARCHAR(50) DEFAULT 'chat',
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ai_agent_messages_session_id ON hrms.ai_agent_messages (session_id);

-- ============================================================================
-- 16. hrms.ai_agent_meeting_bookings (Meeting Bookings from Widget CTA)
-- ============================================================================
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

CREATE INDEX IF NOT EXISTS idx_ai_agent_meetings_email ON hrms.ai_agent_meeting_bookings (email);

-- ============================================================================
-- 17. hrms.ai_agent_support_requests (Support Requests from Widget CTA)
-- ============================================================================
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

CREATE INDEX IF NOT EXISTS idx_ai_agent_support_email ON hrms.ai_agent_support_requests (email);

-- ============================================================================
-- 18. hrms.ai_agent_configs (Agent Persona & Widget Settings)
-- ============================================================================
CREATE TABLE IF NOT EXISTS hrms.ai_agent_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name VARCHAR(100) NOT NULL DEFAULT 'Leslie',
    agent_title VARCHAR(150) NOT NULL DEFAULT 'AI Product & Support Specialist',
    company_name VARCHAR(100) NOT NULL DEFAULT 'Aaralia ',
    avatar_url TEXT,
    video_url TEXT,
    greeting_message TEXT NOT NULL DEFAULT 'Hi! I''m Leslie. How are you currently managing team goals and daily tasks? I can help show how our platform connects strategy to execution smoothly.',
    suggested_questions JSONB NOT NULL DEFAULT '["What are our shift timings?", "Who is available in the engineering department?", "What skills does our team have?", "What is our weekend and calendar policy?"]'::jsonb,
    quick_actions JSONB NOT NULL DEFAULT '[{"id": "book_meeting", "title": "Book a Meeting", "action": "open_modal"}, {"id": "request_support", "title": "Request Support", "action": "open_modal"}]'::jsonb,
    system_prompt TEXT DEFAULT 'You are Leslie, an intelligent AI concierge for Aaralia HRMS. You answer user queries accurately by retrieving real data from the database.',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 19. hrms.attendance_records (Daily Attendance Records)
-- ============================================================================
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

-- ============================================================================
-- 20. hrms.attendance_punches (Punch Clock In/Out Logs)
-- ============================================================================
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

-- ============================================================================
-- 21. hrms.attendance_monthly_stats (Monthly Aggregated Metrics)
-- ============================================================================
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

-- ============================================================================
-- 22. hrms.attendance_audit_log (Audit Trail for Attendance Changes)
-- ============================================================================
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


