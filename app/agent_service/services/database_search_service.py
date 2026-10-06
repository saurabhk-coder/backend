import logging
import re
import time
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class DatabaseSearchService:
    """
    Intelligent Database Search & Retrieval Service for the AI Agent.
    Executes targeted, parameterized queries across HRMS tables:
    - Employees (Personal details, Departments, Roles, Skills, Certifications)
    - Shifts & Working Hours (Timings, Duration, Days, Grace periods)
    - Calendar Settings & Weekend Policies
    - Organization Details & Settings
    """

    def __init__(self):
        self._last_db_error_time = 0.0

    def _should_skip_db(self) -> bool:
        return (time.time() - self._last_db_error_time) < 15.0

    def _mark_db_error(self):
        self._last_db_error_time = time.time()

    def search_employees(self, db: Session, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search employees by name, department, designation, skills, employee_code."""
        if self._should_skip_db():
            return []
        cleaned = f"%{query.strip().lower()}%"
        sql = text("""
            SELECT 
                e.id,
                e.employee_code,
                p.first_name,
                p.last_name,
                p.email,
                p.mobile_number,
                p.city,
                d.department,
                d.designation,
                d.work_location,
                d.work_mode,
                d.reporting_manager,
                prof.skills,
                prof.total_experience_years,
                prof.certifications
            FROM hrms.employees e
            LEFT JOIN hrms.employee_personal_information p ON p.employee_id = e.id
            LEFT JOIN hrms.departments d ON d.employee_id = e.id
            LEFT JOIN hrms.employee_professional_information prof ON prof.employee_id = e.id
            WHERE 
                LOWER(COALESCE(p.first_name, '')) LIKE :q
                OR LOWER(COALESCE(p.last_name, '')) LIKE :q
                OR LOWER(COALESCE(e.employee_code, '')) LIKE :q
                OR LOWER(COALESCE(d.department, '')) LIKE :q
                OR LOWER(COALESCE(d.designation, '')) LIKE :q
                OR LOWER(COALESCE(prof.skills, '')) LIKE :q
                OR LOWER(COALESCE(d.work_location, '')) LIKE :q
            LIMIT :limit
        """)
        try:
            result = db.execute(sql, {"q": cleaned, "limit": limit}).mappings().all()
            return [dict(row) for row in result]
        except Exception as e:
            self._mark_db_error()
            logger.warning(f"Error querying employees: {e}")
            return []

    def search_shifts(self, db: Session, query: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search shift timings, grace periods, and work policies."""
        if self._should_skip_db():
            return []
        sql = text("""
            SELECT 
                s.id,
                s.name,
                TO_CHAR(s.start_time, 'HH24:MI') as start_time,
                TO_CHAR(s.end_time, 'HH24:MI') as end_time,
                s.shift_duration,
                s.department,
                s.location,
                s.weekly_working_days,
                s.is_active,
                g.is_enabled as grace_enabled,
                g.late_check_in_minutes,
                g.early_check_out_minutes
            FROM hrms.shifts s
            LEFT JOIN hrms.shift_grace_periods g ON g.shift_id = s.id
            WHERE (:q IS NULL OR LOWER(s.name) LIKE :q OR LOWER(COALESCE(s.department, '')) LIKE :q)
            ORDER BY s.name ASC
            LIMIT :limit
        """)
        try:
            cleaned = f"%{query.strip().lower()}%" if query and query.strip() else None
            result = db.execute(sql, {"q": cleaned, "limit": limit}).mappings().all()
            return [dict(row) for row in result]
        except Exception as e:
            self._mark_db_error()
            logger.warning(f"Error querying shifts: {e}")
            return []

    def search_calendar_settings(self, db: Session, query: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search calendar settings, working hours, and weekend definitions."""
        if self._should_skip_db():
            return []
        sql = text("""
            SELECT 
                c.id,
                c.location,
                c.is_default,
                c.max_working_hours_per_day,
                c.week_starts_on,
                TO_CHAR(c.shift_start_time, 'HH24:MI') as default_shift_start,
                TO_CHAR(c.shift_end_time, 'HH24:MI') as default_shift_end,
                c.full_day_hours,
                c.half_day_hours,
                c.weekend_definition,
                c.fiscal_year_start_month,
                c.fiscal_year_end_month
            FROM hrms.calendar_settings c
            WHERE (:q IS NULL OR LOWER(c.location) LIKE :q)
            ORDER BY c.is_default DESC
            LIMIT :limit
        """)
        try:
            cleaned = f"%{query.strip().lower()}%" if query and query.strip() else None
            result = db.execute(sql, {"q": cleaned, "limit": limit}).mappings().all()
            return [dict(row) for row in result]
        except Exception as e:
            self._mark_db_error()
            logger.warning(f"Error querying calendar settings: {e}")
            return []

    def search_organizations(self, db: Session, limit: int = 3) -> List[Dict[str, Any]]:
        """Fetch organization profiles and company info."""
        if self._should_skip_db():
            return []
        sql = text("""
            SELECT 
                id,
                name,
                slug,
                email,
                phone,
                city,
                state,
                country,
                status
            FROM hrms.organizations
            LIMIT :limit
        """)
        try:
            result = db.execute(sql, {"limit": limit}).mappings().all()
            return [dict(row) for row in result]
        except Exception as e:
            self._mark_db_error()
            logger.warning(f"Error querying organizations: {e}")
            return []

    def search_users(self, db: Session, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search users and roles."""
        if self._should_skip_db():
            return []
        cleaned = f"%{query.strip().lower()}%"
        sql = text("""
            SELECT 
                u.id,
                u.first_name,
                u.last_name,
                u.email,
                u.status,
                r.name as role_name
            FROM hrms.users u
            LEFT JOIN hrms.roles r ON r.id = u.role_id
            WHERE 
                LOWER(COALESCE(u.first_name, '')) LIKE :q
                OR LOWER(COALESCE(u.last_name, '')) LIKE :q
                OR LOWER(COALESCE(u.email, '')) LIKE :q
                OR LOWER(COALESCE(r.name, '')) LIKE :q
            LIMIT :limit
        """)
        try:
            result = db.execute(sql, {"q": cleaned, "limit": limit}).mappings().all()
            return [dict(row) for row in result]
        except Exception as e:
            self._mark_db_error()
            logger.warning(f"Error querying users: {e}")
            return []

    def comprehensive_search(self, db: Session, user_query: str) -> Dict[str, Any]:
        """
        Executes an intelligent multi-domain search across all relevant tables
        and generates a structured dictionary and readable summary.
        """
        lower = user_query.lower()
        results: Dict[str, Any] = {}

        # 1. Shifts & Working Hours
        if any(w in lower for w in ["shift", "timing", "hours", "late", "grace", "check in", "check-in", "work time", "schedule"]):
            shifts = self.search_shifts(db, query=user_query)
            if not shifts:
                shifts = self.search_shifts(db, query=None)
            results["shifts"] = shifts

        # 2. Calendar & Weekend Policies
        if any(w in lower for w in ["calendar", "weekend", "holiday", "leave", "fiscal", "policy", "sunday", "saturday"]):
            calendars = self.search_calendar_settings(db, query=user_query)
            if not calendars:
                calendars = self.search_calendar_settings(db, query=None)
            results["calendar_settings"] = calendars

        # 3. Employees, Skills, Roles, Team Members
        if any(w in lower for w in ["who", "employee", "team", "person", "developer", "engineer", "manager", "skill", "python", "react", "sales", "hire", "ctc", "role", "designation"]):
            # Extract keywords
            tokens = [t for t in re.findall(r"\w+", lower) if len(t) > 2 and t not in ["who", "the", "and", "for", "with", "are", "what", "find", "show", "tell"]]
            emp_matches: List[Dict[str, Any]] = []
            for token in tokens:
                matches = self.search_employees(db, query=token, limit=5)
                for m in matches:
                    if m not in emp_matches:
                        emp_matches.append(m)
            if not emp_matches:
                emp_matches = self.search_employees(db, query=user_query, limit=5)
            results["employees"] = emp_matches[:5]

        # 4. Organization Info
        if any(w in lower for w in ["company", "organization", "office", "asana", "aaralia", "address", "headquarters"]):
            results["organizations"] = self.search_organizations(db)

        # Fallback: if nothing matched specifically, do a broad lookup
        if not results:
            shifts = self.search_shifts(db, query=user_query, limit=3)
            emps = self.search_employees(db, query=user_query, limit=3)
            if shifts:
                results["shifts"] = shifts
            if emps:
                results["employees"] = emps
            if not shifts and not emps:
                # Include standard organization / shift overview
                results["shifts"] = self.search_shifts(db, limit=3)
                results["organizations"] = self.search_organizations(db, limit=1)

        summary = self._format_summary(results, user_query)
        return {
            "query": user_query,
            "total_found": sum(len(v) for v in results.values() if isinstance(v, list)),
            "results": results,
            "summary": summary,
        }

    def _format_summary(self, results: Dict[str, Any], query: str) -> str:
        """Formats structured database results into conversational text."""
        parts = []

        if "shifts" in results and results["shifts"]:
            shift_strs = []
            for s in results["shifts"]:
                name = s.get("name", "Standard Shift")
                start = s.get("start_time", "09:00")
                end = s.get("end_time", "18:00")
                dur = s.get("shift_duration", "09:00")
                grace = f" (Grace period: {s.get('late_check_in_minutes', 0)} mins late check-in)" if s.get("grace_enabled") else ""
                shift_strs.append(f"• **{name}**: {start} to {end} ({dur} hrs){grace}")
            parts.append("📅 **Shift Schedules in Database:**\n" + "\n".join(shift_strs))

        if "employees" in results and results["employees"]:
            emp_strs = []
            for e in results["employees"]:
                name = f"{e.get('first_name') or ''} {e.get('last_name') or ''}".strip() or "Employee"
                dept = e.get("department") or "Department N/A"
                desig = e.get("designation") or "Role N/A"
                skills = f" | Skills: {e.get('skills')}" if e.get("skills") else ""
                loc = f" ({e.get('work_mode') or 'Onsite'} - {e.get('work_location') or ''})".strip()
                emp_strs.append(f"• **{name}** - {desig}, {dept}{loc}{skills}")
            parts.append("👥 **Employee Directory Results:**\n" + "\n".join(emp_strs))

        if "calendar_settings" in results and results["calendar_settings"]:
            cal_strs = []
            for c in results["calendar_settings"]:
                loc = c.get("location", "All Locations")
                start_day = c.get("week_starts_on", "Monday")
                max_hrs = c.get("max_working_hours_per_day", "09:00")
                cal_strs.append(f"• **{loc}**: Week starts on {start_day}, max working hours: {max_hrs} hrs/day")
            parts.append("🗓️ **Calendar & Policy Settings:**\n" + "\n".join(cal_strs))

        if "organizations" in results and results["organizations"]:
            org_strs = []
            for o in results["organizations"]:
                name = o.get("name", "Organization")
                city = o.get("city") or ""
                country = o.get("country") or ""
                org_strs.append(f"• **{name}** ({city}, {country})")
            parts.append("🏢 **Organization Information:**\n" + "\n".join(org_strs))

        if not parts:
            return "No matching records found in the database for your query. You can book a meeting with our team or submit a support request for assistance!"

        return "\n\n".join(parts)


DATABASE_SEARCH_SERVICE = DatabaseSearchService()
