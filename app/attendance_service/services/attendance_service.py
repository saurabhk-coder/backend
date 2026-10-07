import csv
import io
import math
import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union
from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.employee_service.models import (
    EmployeeDb,
    EmployeeDepartmentInformationDb,
    EmployeePersonalInformationDb,
)
from app.organization_service.models.calendar_setting import CalendarSettingDb
from app.organization_service.models.organization_setting import OrganizationSettingDb
from app.shift_service.models.shift import ShiftDb, ShiftGracePeriodDb
from ..crud.crud_attendance import CRUD_ATTENDANCE, _to_uuid
from ..models.attendance import (
    AttendanceAuditLogDb,
    AttendanceMonthlyStatsDb,
    AttendancePunchDb,
    AttendanceRecordDb,
)
from ..schemas.attendance import (
    AttendanceAuditLogEntry,
    AttendancePunchCreate,
    AttendanceRecordCreate,
    AttendanceRecordResponse,
    AttendanceRecordUpdate,
    KpiCardData,
    MonthlyChartBar,
    PaginationInfo,
    PunchDetail,
    PunchStateData,
    TimelineEvent,
    TimelineSession,
)


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class AttendanceService:
    # -------------------------------------------------------------------------
    # Helper: Organization Settings (Policy & Grace Hours)
    # -------------------------------------------------------------------------
    def get_org_attendance_settings(
        self, db: Session, organization_id: Union[uuid.UUID, str]
    ) -> Tuple[str, int]:
        org_uuid = _to_uuid(organization_id)
        policy = "auto_checkout_at_shift_end"
        grace_hours = 4

        settings = (
            db.query(OrganizationSettingDb)
            .filter(OrganizationSettingDb.organization_id == org_uuid)
            .all()
        )
        for s in settings:
            if s.setting_key == "missingCheckoutPolicy" and s.setting_value:
                policy = s.setting_value.strip()
            elif s.setting_key == "missingCheckoutGraceHours" and s.setting_value:
                try:
                    grace_hours = int(s.setting_value.strip())
                except ValueError:
                    pass

        return policy, grace_hours

    # -------------------------------------------------------------------------
    # Helper: Resolve Shift for Employee / Organization
    # -------------------------------------------------------------------------
    def get_effective_shift(
        self, db: Session, organization_id: Union[uuid.UUID, str], employee_id: int
    ) -> Optional[ShiftDb]:
        org_uuid = _to_uuid(organization_id)

        # Check department first
        dept_info = (
            db.query(EmployeeDepartmentInformationDb)
            .filter(EmployeeDepartmentInformationDb.employee_id == employee_id)
            .first()
        )
        if dept_info and dept_info.department:
            shift = (
                db.query(ShiftDb)
                .filter(
                    ShiftDb.organization_id == org_uuid,
                    ShiftDb.department == dept_info.department,
                    ShiftDb.is_active == True,
                )
                .first()
            )
            if shift:
                return shift

        # Fallback to default active shift in organization
        shift = (
            db.query(ShiftDb)
            .filter(
                ShiftDb.organization_id == org_uuid,
                ShiftDb.is_active == True,
            )
            .first()
        )
        return shift

    # -------------------------------------------------------------------------
    # Missing Checkout Auto-Checkout Condition
    # -------------------------------------------------------------------------
    def check_and_apply_auto_checkout(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        record: AttendanceRecordDb,
        shift: Optional[ShiftDb] = None,
    ) -> bool:
        if not record or record.check_in is None or record.check_out is not None or record.auto_checked_out:
            return False

        org_uuid = _to_uuid(organization_id)
        now_utc = datetime.now(timezone.utc)
        record_date = record.date
        today_date = now_utc.date()

        policy, grace_hours = self.get_org_attendance_settings(db, org_uuid)

        # Determine shift end time
        shift_end_t = shift.end_time if shift and shift.end_time else time(18, 0)
        record_shift_end = datetime.combine(record_date, shift_end_t, tzinfo=timezone.utc)
        trigger_time = record_shift_end + timedelta(hours=grace_hours)

        if now_utc >= trigger_time or record_date < today_date:
            old_vals = {
                "check_out": None,
                "status": record.status,
                "production_hours": float(record.production_hours) if record.production_hours else 0.0,
                "auto_checked_out": False,
            }

            if policy == "mark_half_day":
                record.status = "Half Day"
                half_day_hrs = 4.0
                if shift and shift.half_day_hours:
                    try:
                        h, m = map(int, shift.half_day_hours.split(":"))
                        half_day_hrs = h + m / 60.0
                    except Exception:
                        pass
                record.production_hours = Decimal(f"{half_day_hrs:.2f}")
                record.total_work_minutes = int(half_day_hrs * 60)
            else:
                # Default: auto_checkout_at_shift_end
                record.check_out = record_shift_end
                work_mins = max(0, int((_ensure_utc(record.check_out) - _ensure_utc(record.check_in)).total_seconds() / 60) - record.break_minutes)
                record.total_work_minutes = work_mins
                record.production_hours = Decimal(f"{work_mins / 60.0:.2f}")

                # Determine status
                full_day_mins = 480
                tolerance_mins = 0
                if shift and shift.full_day_hours:
                    try:
                        h, m = map(int, shift.full_day_hours.split(":"))
                        full_day_mins = h * 60 + m
                    except Exception:
                        pass
                if shift and shift.full_day_tolerance:
                    try:
                        h, m = map(int, shift.full_day_tolerance.split(":"))
                        tolerance_mins = h * 60 + m
                    except Exception:
                        pass

                if work_mins >= (full_day_mins - tolerance_mins):
                    record.status = "Present"
                elif work_mins >= 240:
                    record.status = "Half Day"
                else:
                    record.status = "Absent"

            record.auto_checked_out = True
            record.updated_at = now_utc

            # Write Audit Log
            audit = AttendanceAuditLogDb(
                organization_id=org_uuid,
                attendance_record_id=record.id,
                employee_id=record.employee_id,
                action="auto_checkout",
                old_values=old_vals,
                new_values={
                    "check_out": record.check_out.isoformat() if record.check_out else None,
                    "status": record.status,
                    "production_hours": float(record.production_hours) if record.production_hours else 0.0,
                    "auto_checked_out": True,
                },
                reason=f"Missing checkout policy '{policy}' triggered after shift end + {grace_hours}h grace",
                changed_by="system",
                changed_at=now_utc,
            )
            db.add(audit)
            db.commit()
            db.refresh(record)
            return True

        return False

    # -------------------------------------------------------------------------
    # Recalculate Attendance Record from Punches
    # -------------------------------------------------------------------------
    def recalculate_record_from_punches(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        record: AttendanceRecordDb,
        shift: Optional[ShiftDb] = None,
    ):
        punches = (
            db.query(AttendancePunchDb)
            .filter(AttendancePunchDb.attendance_record_id == record.id)
            .order_by(AttendancePunchDb.punch_time.asc())
            .all()
        )

        if not punches:
            record.check_in = None
            record.check_out = None
            record.total_work_minutes = 0
            record.break_minutes = 0
            record.production_hours = Decimal("0.00")
            record.overtime_hours = Decimal("0.00")
            record.late_minutes = 0
            record.status = "Absent"
            db.commit()
            return

        in_punches = [p for p in punches if p.punch_type.upper() == "IN"]
        out_punches = [p for p in punches if p.punch_type.upper() == "OUT"]

        first_in = in_punches[0].punch_time if in_punches else None
        last_out = out_punches[-1].punch_time if out_punches else None

        record.check_in = first_in
        # If currently clocked in, check_out is None; otherwise last_out
        if punches[-1].punch_type.upper() == "IN":
            record.check_out = None
        else:
            record.check_out = last_out

        # Compute total work minutes across pairs of IN -> OUT
        total_worked_seconds = 0
        total_break_seconds = 0
        last_out_time = None
        current_in = None

        for p in punches:
            pt = p.punch_type.upper()
            if pt == "IN":
                current_in = p.punch_time
                if last_out_time:
                    total_break_seconds += max(0, (_ensure_utc(current_in) - _ensure_utc(last_out_time)).total_seconds())
                    last_out_time = None
            elif pt == "OUT" and current_in:
                total_worked_seconds += max(0, (_ensure_utc(p.punch_time) - _ensure_utc(current_in)).total_seconds())
                last_out_time = p.punch_time
                current_in = None

        # If currently punched in today, count live time up to now
        if current_in and record.date == datetime.now(timezone.utc).date():
            total_worked_seconds += max(0, (datetime.now(timezone.utc) - _ensure_utc(current_in)).total_seconds())

        work_minutes = int(total_worked_seconds / 60)
        break_minutes = int(total_break_seconds / 60)
        production_hours = round(work_minutes / 60.0, 2)

        record.total_work_minutes = work_minutes
        record.break_minutes = break_minutes
        record.production_hours = Decimal(f"{production_hours:.2f}")

        # Late Calculation
        late_minutes = 0
        if first_in:
            shift_start_t = shift.start_time if shift and shift.start_time else time(9, 0)
            grace_mins = 0
            if shift and shift.grace_period and shift.grace_period.is_enabled:
                grace_mins = shift.grace_period.late_check_in_minutes

            first_in_t = first_in.time()
            shift_start_delta = timedelta(hours=shift_start_t.hour, minutes=shift_start_t.minute)
            check_in_delta = timedelta(hours=first_in_t.hour, minutes=first_in_t.minute, seconds=first_in_t.second)
            diff_mins = int((check_in_delta - shift_start_delta).total_seconds() / 60)
            if diff_mins > grace_mins:
                late_minutes = diff_mins - grace_mins

        record.late_minutes = max(0, late_minutes)

        # Status & Overtime determination
        full_day_mins = 480
        tolerance_mins = 0
        half_day_mins = 240
        shift_length_hours = 9.0

        if shift:
            if shift.full_day_hours:
                try:
                    h, m = map(int, shift.full_day_hours.split(":"))
                    full_day_mins = h * 60 + m
                except Exception:
                    pass
            if shift.full_day_tolerance:
                try:
                    h, m = map(int, shift.full_day_tolerance.split(":"))
                    tolerance_mins = h * 60 + m
                except Exception:
                    pass
            if shift.half_day_hours:
                try:
                    h, m = map(int, shift.half_day_hours.split(":"))
                    half_day_mins = h * 60 + m
                except Exception:
                    pass
            if shift.shift_duration:
                try:
                    h, m = map(int, shift.shift_duration.split(":"))
                    shift_length_hours = h + m / 60.0
                except Exception:
                    pass

        # Overtime
        if production_hours > shift_length_hours:
            ot = round(production_hours - shift_length_hours, 2)
            record.overtime_hours = Decimal(f"{ot:.2f}")
        else:
            record.overtime_hours = Decimal("0.00")

        # Present / Half Day / Late / Absent status
        if work_minutes >= (full_day_mins - tolerance_mins):
            record.status = "Present"
        elif work_minutes >= half_day_mins:
            record.status = "Half Day"
        elif first_in is not None:
            record.status = "Present" if record.date == datetime.now(timezone.utc).date() else "Half Day"
        else:
            record.status = "Absent"

        record.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(record)

    # -------------------------------------------------------------------------
    # Get or Create Daily Record
    # -------------------------------------------------------------------------
    def get_or_create_daily_record(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        employee_id: int,
        record_date: date,
        shift: Optional[ShiftDb] = None,
    ) -> AttendanceRecordDb:
        org_uuid = _to_uuid(organization_id)
        record = (
            db.query(AttendanceRecordDb)
            .filter(
                AttendanceRecordDb.organization_id == org_uuid,
                AttendanceRecordDb.employee_id == employee_id,
                AttendanceRecordDb.date == record_date,
            )
            .first()
        )
        if not record:
            record = AttendanceRecordDb(
                organization_id=org_uuid,
                employee_id=employee_id,
                date=record_date,
                shift_id=shift.id if shift else None,
                status="Absent",
            )
            db.add(record)
            db.commit()
            db.refresh(record)

        self.check_and_apply_auto_checkout(db, org_uuid, record, shift)
        return record

    # -------------------------------------------------------------------------
    # 1. GET /attendance/punch-state
    # -------------------------------------------------------------------------
    def get_punch_state(
        self, db: Session, organization_id: Union[uuid.UUID, str], employee_id: int
    ) -> PunchStateData:
        today_date = datetime.now(timezone.utc).date()
        shift = self.get_effective_shift(db, organization_id, employee_id)
        record = self.get_or_create_daily_record(db, organization_id, employee_id, today_date, shift)

        punches = (
            db.query(AttendancePunchDb)
            .filter(AttendancePunchDb.attendance_record_id == record.id)
            .order_by(AttendancePunchDb.punch_time.asc())
            .all()
        )

        is_punched_in = False
        last_in_time = None
        if punches:
            last_punch = punches[-1]
            if last_punch.punch_type.upper() == "IN":
                is_punched_in = True
                last_in_time = last_punch.punch_time

        current_session_mins = 0
        if is_punched_in and last_in_time:
            now_utc = datetime.now(timezone.utc)
            current_session_mins = max(0, int((now_utc - _ensure_utc(last_in_time)).total_seconds() / 60))

        prod_hours = float(record.production_hours) if record.production_hours else 0.0
        full_day_mins = 480
        shift_len = 9.0
        if shift:
            if shift.full_day_hours:
                try:
                    h, m = map(int, shift.full_day_hours.split(":"))
                    full_day_mins = h * 60 + m
                except Exception:
                    pass
            if shift.shift_duration:
                try:
                    h, m = map(int, shift.shift_duration.split(":"))
                    shift_len = h + m / 60.0
                except Exception:
                    pass

        full_day_hrs = full_day_mins / 60.0
        if prod_hours < full_day_hrs:
            indicator = "low"
        elif prod_hours <= shift_len:
            indicator = "neutral"
        else:
            indicator = "overtime"

        shift_info = None
        if shift:
            shift_info = {
                "id": str(shift.id),
                "name": shift.name,
                "startTime": shift.start_time.isoformat() if shift.start_time else "09:00",
                "endTime": shift.end_time.isoformat() if shift.end_time else "18:00",
                "duration": shift.shift_duration or "09:00",
            }

        return PunchStateData(
            isPunchedIn=is_punched_in,
            date=today_date,
            firstCheckIn=record.check_in,
            lastCheckOut=record.check_out,
            currentSessionMinutes=current_session_mins,
            totalWorkMinutes=record.total_work_minutes or 0,
            totalWorkHours=prod_hours,
            breakMinutes=record.break_minutes or 0,
            status=record.status or "Absent",
            punchesCount=len(punches),
            productionIndicator=indicator,
            shiftInfo=shift_info,
        )

    # -------------------------------------------------------------------------
    # 2. POST /attendance/punch
    # -------------------------------------------------------------------------
    def record_punch(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        employee_id: int,
        punch_type_req: Optional[str] = "toggle",
        note: Optional[str] = None,
        location: Optional[str] = None,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[PunchStateData, str]:
        today_date = datetime.now(timezone.utc).date()
        shift = self.get_effective_shift(db, organization_id, employee_id)
        record = self.get_or_create_daily_record(db, organization_id, employee_id, today_date, shift)

        punches = (
            db.query(AttendancePunchDb)
            .filter(AttendancePunchDb.attendance_record_id == record.id)
            .order_by(AttendancePunchDb.punch_time.asc())
            .all()
        )

        currently_in = False
        if punches and punches[-1].punch_type.upper() == "IN":
            currently_in = True

        action_type = (punch_type_req or "toggle").strip().lower()
        if action_type == "toggle":
            actual_type = "OUT" if currently_in else "IN"
        elif action_type in ("in", "checkin", "check_in"):
            actual_type = "IN"
        elif action_type in ("out", "checkout", "check_out"):
            actual_type = "OUT"
        else:
            actual_type = "OUT" if currently_in else "IN"

        server_now = datetime.now(timezone.utc)

        new_punch = AttendancePunchDb(
            organization_id=_to_uuid(organization_id),
            attendance_record_id=record.id,
            employee_id=employee_id,
            punch_time=server_now,
            punch_type=actual_type,
            location=location,
            device_info=device_info,
            ip_address=ip_address,
            note=note,
        )
        db.add(new_punch)
        db.commit()

        self.recalculate_record_from_punches(db, organization_id, record, shift)

        state_data = self.get_punch_state(db, organization_id, employee_id)
        msg = f"Successfully punched {actual_type.lower()} at {server_now.strftime('%H:%M:%S UTC')}"
        return state_data, msg

    # -------------------------------------------------------------------------
    # 3. GET /attendance/summary/my
    # -------------------------------------------------------------------------
    def get_employee_summary(
        self, db: Session, organization_id: Union[uuid.UUID, str], employee_id: int
    ) -> Dict[str, Any]:
        org_uuid = _to_uuid(organization_id)
        now_utc = datetime.now(timezone.utc)
        today_date = now_utc.date()
        start_of_week = today_date - timedelta(days=today_date.weekday())
        start_of_month = date(today_date.year, today_date.month, 1)

        shift = self.get_effective_shift(db, org_uuid, employee_id)
        today_record = self.get_or_create_daily_record(db, org_uuid, employee_id, today_date, shift)

        today_punches = (
            db.query(AttendancePunchDb)
            .filter(AttendancePunchDb.attendance_record_id == today_record.id)
            .order_by(AttendancePunchDb.punch_time.asc())
            .all()
        )

        today_work_hours = float(today_record.production_hours) if today_record.production_hours else 0.0

        week_records = (
            db.query(AttendanceRecordDb)
            .filter(
                AttendanceRecordDb.organization_id == org_uuid,
                AttendanceRecordDb.employee_id == employee_id,
                AttendanceRecordDb.date >= start_of_week,
                AttendanceRecordDb.date <= today_date,
            )
            .all()
        )
        weekly_hours = round(sum(float(r.production_hours or 0.0) for r in week_records), 2)

        month_records = (
            db.query(AttendanceRecordDb)
            .filter(
                AttendanceRecordDb.organization_id == org_uuid,
                AttendanceRecordDb.employee_id == employee_id,
                AttendanceRecordDb.date >= start_of_month,
                AttendanceRecordDb.date <= today_date,
            )
            .all()
        )
        monthly_hours = round(sum(float(r.production_hours or 0.0) for r in month_records), 2)
        overtime_hours = round(sum(float(r.overtime_hours or 0.0) for r in month_records), 2)

        timeline_events = [
            TimelineEvent(
                id=p.id,
                time=p.punch_time,
                punchType=p.punch_type,
                note=p.note,
                location=p.location,
            )
            for p in today_punches
        ]

        sessions = []
        cur_in = None
        s_num = 1
        for p in today_punches:
            if p.punch_type.upper() == "IN":
                cur_in = p.punch_time
            elif p.punch_type.upper() == "OUT" and cur_in:
                dur_m = max(0, int((_ensure_utc(p.punch_time) - _ensure_utc(cur_in)).total_seconds() / 60))
                sessions.append(
                    TimelineSession(
                        sessionNumber=s_num,
                        checkIn=cur_in,
                        checkOut=p.punch_time,
                        durationMinutes=dur_m,
                        durationHours=round(dur_m / 60.0, 2),
                    )
                )
                s_num += 1
                cur_in = None

        if cur_in:
            dur_m = max(0, int((now_utc - _ensure_utc(cur_in)).total_seconds() / 60))
            sessions.append(
                TimelineSession(
                    sessionNumber=s_num,
                    checkIn=cur_in,
                    checkOut=None,
                    durationMinutes=dur_m,
                    durationHours=round(dur_m / 60.0, 2),
                )
            )

        return {
            "todayWorkHours": today_work_hours,
            "weeklyWorkHours": weekly_hours,
            "monthlyWorkHours": monthly_hours,
            "overtimeHours": overtime_hours,
            "todayTimeline": timeline_events,
            "sessions": sessions,
        }

    # -------------------------------------------------------------------------
    # 4. GET /attendance/records & /attendance/history/my
    # -------------------------------------------------------------------------
    def get_attendance_records(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        employee_ids: Optional[List[int]] = None,
        date_filter: Optional[date] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "date",
        sort_order: str = "desc",
    ) -> Tuple[List[AttendanceRecordResponse], PaginationInfo]:
        org_uuid = _to_uuid(organization_id)
        query = db.query(AttendanceRecordDb).filter(
            AttendanceRecordDb.organization_id == org_uuid
        )

        if employee_ids is not None:
            query = query.filter(AttendanceRecordDb.employee_id.in_(employee_ids))

        if date_filter:
            query = query.filter(AttendanceRecordDb.date == date_filter)
        else:
            if start_date:
                query = query.filter(AttendanceRecordDb.date >= start_date)
            if end_date:
                query = query.filter(AttendanceRecordDb.date <= end_date)
            if year and not start_date and not end_date:
                query = query.filter(func.extract("year", AttendanceRecordDb.date) == year)
            if month and not start_date and not end_date:
                query = query.filter(func.extract("month", AttendanceRecordDb.date) == month)

        if status_filter:
            query = query.filter(AttendanceRecordDb.status.ilike(status_filter.strip()))

        # Search by employee name or code if specified
        if search:
            search_pattern = f"%{search.strip()}%"
            matched_emp_ids = [
                r[0]
                for r in db.query(EmployeePersonalInformationDb.employee_id)
                .filter(
                    EmployeePersonalInformationDb.organization_id == org_uuid,
                    or_(
                        EmployeePersonalInformationDb.first_name.ilike(search_pattern),
                        EmployeePersonalInformationDb.last_name.ilike(search_pattern),
                        EmployeePersonalInformationDb.email.ilike(search_pattern),
                    ),
                )
                .all()
            ]
            query = query.filter(AttendanceRecordDb.employee_id.in_(matched_emp_ids))

        total = query.count()
        total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1

        sort_col = getattr(AttendanceRecordDb, sort_by, AttendanceRecordDb.date)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        records = query.offset((page - 1) * page_size).limit(page_size).all()

        emp_ids = list(set(r.employee_id for r in records))
        emp_map = self._get_employees_meta_map(db, org_uuid, emp_ids)

        items = []
        for r in records:
            emp_info = emp_map.get(r.employee_id, {})
            prod_hrs = float(r.production_hours) if r.production_hours else 0.0
            ind = "low" if prod_hrs < 8.0 else ("neutral" if prod_hrs <= 9.0 else "overtime")

            items.append(
                AttendanceRecordResponse(
                    id=r.id,
                    employeeId=r.employee_id,
                    employeeName=emp_info.get("name"),
                    employeeCode=emp_info.get("code"),
                    department=emp_info.get("department"),
                    designation=emp_info.get("designation"),
                    avatar=emp_info.get("avatar"),
                    date=r.date,
                    checkIn=r.check_in,
                    checkOut=r.check_out,
                    totalWorkMinutes=r.total_work_minutes or 0,
                    breakMinutes=r.break_minutes or 0,
                    productionHours=prod_hrs,
                    overtimeHours=float(r.overtime_hours or 0.0),
                    lateMinutes=r.late_minutes or 0,
                    earlyLeaveMinutes=r.early_leave_minutes or 0,
                    status=r.status or "Absent",
                    autoCheckedOut=bool(r.auto_checked_out),
                    productionIndicator=ind,
                    notes=r.notes,
                )
            )

        pagination = PaginationInfo(
            page=page,
            pageSize=page_size,
            total=total,
            totalPages=total_pages,
        )
        return items, pagination

    def _get_employees_meta_map(
        self, db: Session, organization_id: uuid.UUID, employee_ids: List[int]
    ) -> Dict[int, Dict[str, Any]]:
        if not employee_ids:
            return {}

        personal_rows = (
            db.query(EmployeePersonalInformationDb)
            .filter(
                EmployeePersonalInformationDb.organization_id == organization_id,
                EmployeePersonalInformationDb.employee_id.in_(employee_ids),
            )
            .all()
        )
        dept_rows = (
            db.query(EmployeeDepartmentInformationDb)
            .filter(EmployeeDepartmentInformationDb.employee_id.in_(employee_ids))
            .all()
        )
        emp_code_rows = (
            db.query(EmployeeDb)
            .filter(EmployeeDb.id.in_(employee_ids))
            .all()
        )

        meta: Dict[int, Dict[str, Any]] = {}
        for eid in employee_ids:
            meta[eid] = {
                "name": f"Employee #{eid}",
                "code": f"EMP-{eid:03d}",
                "department": "General",
                "designation": "Staff",
                "avatar": None,
            }

        for p in personal_rows:
            full_name = f"{p.first_name} {p.last_name or ''}".strip()
            meta[p.employee_id]["name"] = full_name or meta[p.employee_id]["name"]
            meta[p.employee_id]["avatar"] = p.profile_photo

        for d in dept_rows:
            if d.department:
                meta[d.employee_id]["department"] = d.department
            if d.designation:
                meta[d.employee_id]["designation"] = d.designation

        for c in emp_code_rows:
            if c.employee_code:
                meta[c.id]["code"] = c.employee_code

        return meta

    # -------------------------------------------------------------------------
    # Get Single Record
    # -------------------------------------------------------------------------
    def get_single_record(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        record_id: Union[uuid.UUID, str],
    ) -> AttendanceRecordResponse:
        record = CRUD_ATTENDANCE.get(db, record_id, organization_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attendance record with ID '{record_id}' not found",
            )

        emp_map = self._get_employees_meta_map(db, record.organization_id, [record.employee_id])
        emp_info = emp_map.get(record.employee_id, {})
        prod_hrs = float(record.production_hours) if record.production_hours else 0.0
        ind = "low" if prod_hrs < 8.0 else ("neutral" if prod_hrs <= 9.0 else "overtime")

        return AttendanceRecordResponse(
            id=record.id,
            employeeId=record.employee_id,
            employeeName=emp_info.get("name"),
            employeeCode=emp_info.get("code"),
            department=emp_info.get("department"),
            designation=emp_info.get("designation"),
            avatar=emp_info.get("avatar"),
            date=record.date,
            checkIn=record.check_in,
            checkOut=record.check_out,
            totalWorkMinutes=record.total_work_minutes or 0,
            breakMinutes=record.break_minutes or 0,
            productionHours=prod_hrs,
            overtimeHours=float(record.overtime_hours or 0.0),
            lateMinutes=record.late_minutes or 0,
            earlyLeaveMinutes=record.early_leave_minutes or 0,
            status=record.status or "Absent",
            autoCheckedOut=bool(record.auto_checked_out),
            productionIndicator=ind,
            notes=record.notes,
        )

    # -------------------------------------------------------------------------
    # Manual Create Attendance Record
    # -------------------------------------------------------------------------
    def create_manual_record(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        payload: AttendanceRecordCreate,
        changed_by: str = "admin",
    ) -> AttendanceRecordResponse:
        org_uuid = _to_uuid(organization_id)
        existing = CRUD_ATTENDANCE.get_by_employee_and_date(
            db, org_uuid, payload.employeeId, payload.date
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Attendance record already exists for employee {payload.employeeId} on date {payload.date}",
            )

        shift = self.get_effective_shift(db, org_uuid, payload.employeeId)
        record = CRUD_ATTENDANCE.create(db, org_uuid, payload)

        if payload.checkIn and payload.checkOut:
            work_mins = max(0, int((_ensure_utc(payload.checkOut) - _ensure_utc(payload.checkIn)).total_seconds() / 60))
            record.total_work_minutes = work_mins
            prod_hrs = round(work_mins / 60.0, 2)
            record.production_hours = Decimal(f"{prod_hrs:.2f}")

            # Overtime check
            shift_len = 9.0
            if shift and shift.shift_duration:
                try:
                    h, m = map(int, shift.shift_duration.split(":"))
                    shift_len = h + m / 60.0
                except Exception:
                    pass
            if prod_hrs > shift_len:
                record.overtime_hours = Decimal(f"{round(prod_hrs - shift_len, 2):.2f}")

            # Late check
            if shift and shift.start_time:
                s_delta = timedelta(hours=shift.start_time.hour, minutes=shift.start_time.minute)
                c_delta = timedelta(hours=payload.checkIn.hour, minutes=payload.checkIn.minute)
                diff = int((c_delta - s_delta).total_seconds() / 60)
                grace = shift.grace_period.late_check_in_minutes if shift.grace_period and shift.grace_period.is_enabled else 0
                record.late_minutes = max(0, diff - grace)

            db.commit()
            db.refresh(record)

        CRUD_ATTENDANCE.create_audit_log(
            db=db,
            organization_id=org_uuid,
            employee_id=payload.employeeId,
            action="manual_create",
            old_values={},
            new_values={
                "date": payload.date.isoformat(),
                "checkIn": payload.checkIn.isoformat() if payload.checkIn else None,
                "checkOut": payload.checkOut.isoformat() if payload.checkOut else None,
                "status": record.status,
            },
            attendance_record_id=record.id,
            reason=payload.reason or "Manual attendance record creation",
            changed_by=changed_by,
        )

        return self.get_single_record(db, org_uuid, record.id)

    # -------------------------------------------------------------------------
    # Manual Update Attendance Record
    # -------------------------------------------------------------------------
    def update_manual_record(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        record_id: Union[uuid.UUID, str],
        payload: AttendanceRecordUpdate,
        changed_by: str = "admin",
    ) -> AttendanceRecordResponse:
        record = CRUD_ATTENDANCE.get(db, record_id, organization_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attendance record with ID '{record_id}' not found",
            )

        old_values = {
            "checkIn": record.check_in.isoformat() if record.check_in else None,
            "checkOut": record.check_out.isoformat() if record.check_out else None,
            "status": record.status,
            "notes": record.notes,
            "totalWorkMinutes": record.total_work_minutes,
            "productionHours": float(record.production_hours) if record.production_hours else 0.0,
        }

        record = CRUD_ATTENDANCE.update(db, record, payload)

        # Recalculate work hours if checkIn / checkOut modified
        if record.check_in and record.check_out:
            work_mins = max(0, int((_ensure_utc(record.check_out) - _ensure_utc(record.check_in)).total_seconds() / 60) - (record.break_minutes or 0))
            record.total_work_minutes = work_mins
            prod_hrs = round(work_mins / 60.0, 2)
            record.production_hours = Decimal(f"{prod_hrs:.2f}")

            shift = self.get_effective_shift(db, record.organization_id, record.employee_id)
            shift_len = 9.0
            if shift and shift.shift_duration:
                try:
                    h, m = map(int, shift.shift_duration.split(":"))
                    shift_len = h + m / 60.0
                except Exception:
                    pass
            if prod_hrs > shift_len:
                record.overtime_hours = Decimal(f"{round(prod_hrs - shift_len, 2):.2f}")
            else:
                record.overtime_hours = Decimal("0.00")

            if shift and shift.start_time:
                s_delta = timedelta(hours=shift.start_time.hour, minutes=shift.start_time.minute)
                c_delta = timedelta(hours=record.check_in.hour, minutes=record.check_in.minute)
                diff = int((c_delta - s_delta).total_seconds() / 60)
                grace = shift.grace_period.late_check_in_minutes if shift.grace_period and shift.grace_period.is_enabled else 0
                record.late_minutes = max(0, diff - grace)

            db.commit()
            db.refresh(record)

        new_values = {
            "checkIn": record.check_in.isoformat() if record.check_in else None,
            "checkOut": record.check_out.isoformat() if record.check_out else None,
            "status": record.status,
            "notes": record.notes,
            "totalWorkMinutes": record.total_work_minutes,
            "productionHours": float(record.production_hours) if record.production_hours else 0.0,
        }

        CRUD_ATTENDANCE.create_audit_log(
            db=db,
            organization_id=record.organization_id,
            employee_id=record.employee_id,
            action="manual_update",
            old_values=old_values,
            new_values=new_values,
            attendance_record_id=record.id,
            reason=payload.reason or "Manual attendance update",
            changed_by=changed_by,
        )

        return self.get_single_record(db, record.organization_id, record.id)

    # -------------------------------------------------------------------------
    # Delete Record
    # -------------------------------------------------------------------------
    def delete_record(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        record_id: Union[uuid.UUID, str],
    ) -> None:
        record = CRUD_ATTENDANCE.get(db, record_id, organization_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attendance record with ID '{record_id}' not found",
            )
        CRUD_ATTENDANCE.remove(db, record)

    # -------------------------------------------------------------------------
    # Record Punches Management
    # -------------------------------------------------------------------------
    def get_record_punches(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        record_id: Union[uuid.UUID, str],
    ) -> List[PunchDetail]:
        record = CRUD_ATTENDANCE.get(db, record_id, organization_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attendance record with ID '{record_id}' not found",
            )

        punches = CRUD_ATTENDANCE.get_punches(db, record_id)
        return [
            PunchDetail(
                id=p.id,
                punchTime=p.punch_time,
                punchType=p.punch_type,
                location=p.location,
                note=p.note,
            )
            for p in punches
        ]

    def add_manual_punch(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        record_id: Union[uuid.UUID, str],
        payload: AttendancePunchCreate,
        changed_by: str = "admin",
    ) -> PunchDetail:
        record = CRUD_ATTENDANCE.get(db, record_id, organization_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attendance record with ID '{record_id}' not found",
            )

        punch_time = payload.punchTime or datetime.now(timezone.utc)
        punch = CRUD_ATTENDANCE.create_punch(
            db=db,
            organization_id=organization_id,
            employee_id=record.employee_id,
            record_id=record.id,
            punch_type=payload.punchType,
            punch_time=punch_time,
            location=payload.location,
            device_info=payload.deviceInfo,
            note=payload.note,
        )

        shift = self.get_effective_shift(db, organization_id, record.employee_id)
        self.recalculate_record_from_punches(db, organization_id, record, shift)

        CRUD_ATTENDANCE.create_audit_log(
            db=db,
            organization_id=organization_id,
            employee_id=record.employee_id,
            action="manual_punch_add",
            old_values={},
            new_values={
                "punchId": str(punch.id),
                "punchTime": punch.punch_time.isoformat(),
                "punchType": punch.punch_type,
            },
            attendance_record_id=record.id,
            reason=payload.note or "Manual punch addition",
            changed_by=changed_by,
        )

        return PunchDetail(
            id=punch.id,
            punchTime=punch.punch_time,
            punchType=punch.punch_type,
            location=punch.location,
            note=punch.note,
        )

    def delete_punch(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        punch_id: Union[uuid.UUID, str],
        changed_by: str = "admin",
    ) -> None:
        punch = CRUD_ATTENDANCE.get_punch(db, punch_id, organization_id)
        if not punch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attendance punch with ID '{punch_id}' not found",
            )

        record = CRUD_ATTENDANCE.get(db, punch.attendance_record_id, organization_id)
        old_val = {
            "punchId": str(punch.id),
            "punchTime": punch.punch_time.isoformat(),
            "punchType": punch.punch_type,
        }

        CRUD_ATTENDANCE.delete_punch(db, punch)

        if record:
            shift = self.get_effective_shift(db, organization_id, record.employee_id)
            self.recalculate_record_from_punches(db, organization_id, record, shift)

            CRUD_ATTENDANCE.create_audit_log(
                db=db,
                organization_id=organization_id,
                employee_id=record.employee_id,
                action="manual_punch_delete",
                old_values=old_val,
                new_values={},
                attendance_record_id=record.id,
                reason="Manual punch deletion",
                changed_by=changed_by,
            )

    # -------------------------------------------------------------------------
    # Auto-Checkout Evaluation Job
    # -------------------------------------------------------------------------
    def run_auto_checkout_job(
        self,
        db: Session,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> Tuple[int, int]:
        query = db.query(AttendanceRecordDb).filter(
            AttendanceRecordDb.check_in.isnot(None),
            AttendanceRecordDb.check_out.is_(None),
            AttendanceRecordDb.auto_checked_out == False,
        )
        if organization_id is not None:
            query = query.filter(AttendanceRecordDb.organization_id == _to_uuid(organization_id))

        pending_records = query.all()
        processed_count = len(pending_records)
        auto_checked_count = 0

        for r in pending_records:
            shift = self.get_effective_shift(db, r.organization_id, r.employee_id)
            applied = self.check_and_apply_auto_checkout(db, r.organization_id, r, shift)
            if applied:
                auto_checked_count += 1

        return processed_count, auto_checked_count

    # -------------------------------------------------------------------------
    # Audit Logs Retrieval
    # -------------------------------------------------------------------------
    def get_audit_logs(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        attendance_record_id: Optional[Union[uuid.UUID, str]] = None,
        employee_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[AttendanceAuditLogEntry], PaginationInfo]:
        logs, total = CRUD_ATTENDANCE.get_audit_logs(
            db, organization_id, attendance_record_id, employee_id, page, page_size
        )
        total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1

        entries = [
            AttendanceAuditLogEntry(
                id=log.id,
                attendanceRecordId=log.attendance_record_id,
                employeeId=log.employee_id,
                action=log.action,
                oldValues=log.old_values or {},
                newValues=log.new_values or {},
                reason=log.reason,
                changedBy=log.changed_by,
                changedAt=log.changed_at,
            )
            for log in logs
        ]

        pagination = PaginationInfo(
            page=page,
            pageSize=page_size,
            total=total,
            totalPages=total_pages,
        )
        return entries, pagination

    # -------------------------------------------------------------------------
    # 5. GET /attendance/report/kpis
    # -------------------------------------------------------------------------
    def get_report_kpis(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        mode: str = "average",
        month: Optional[int] = None,
        year: Optional[int] = None,
        department: Optional[str] = None,
    ) -> Dict[str, KpiCardData]:
        org_uuid = _to_uuid(organization_id)
        now = datetime.now(timezone.utc)
        curr_year = year or now.year
        curr_month = month or now.month

        prev_year = curr_year if curr_month > 1 else curr_year - 1
        prev_month = curr_month - 1 if curr_month > 1 else 12

        emp_query = db.query(EmployeePersonalInformationDb.employee_id).filter(
            EmployeePersonalInformationDb.organization_id == org_uuid
        )
        if department:
            emp_query = emp_query.join(
                EmployeeDepartmentInformationDb,
                EmployeeDepartmentInformationDb.employee_id == EmployeePersonalInformationDb.employee_id,
            ).filter(EmployeeDepartmentInformationDb.department == department)

        active_emp_ids = [r[0] for r in emp_query.all()]
        emp_count = max(1, len(active_emp_ids))

        curr_records = (
            db.query(AttendanceRecordDb)
            .filter(
                AttendanceRecordDb.organization_id == org_uuid,
                AttendanceRecordDb.employee_id.in_(active_emp_ids) if active_emp_ids else True,
                func.extract("year", AttendanceRecordDb.date) == curr_year,
                func.extract("month", AttendanceRecordDb.date) == curr_month,
            )
            .all()
        )

        prev_records = (
            db.query(AttendanceRecordDb)
            .filter(
                AttendanceRecordDb.organization_id == org_uuid,
                AttendanceRecordDb.employee_id.in_(active_emp_ids) if active_emp_ids else True,
                func.extract("year", AttendanceRecordDb.date) == prev_year,
                func.extract("month", AttendanceRecordDb.date) == prev_month,
            )
            .all()
        )

        def calc_metrics(records_list: List[AttendanceRecordDb]):
            present_c = sum(1 for r in records_list if r.status == "Present")
            absent_c = sum(1 for r in records_list if r.status == "Absent")
            late_c = sum(1 for r in records_list if (r.late_minutes and r.late_minutes > 0) or r.status == "Late")
            half_c = sum(1 for r in records_list if r.status == "Half Day")
            return present_c, absent_c, late_c, half_c

        c_pres, c_abs, c_late, c_half = calc_metrics(curr_records)
        p_pres, p_abs, p_late, p_half = calc_metrics(prev_records)

        def make_card(title: str, curr_val: int, prev_val: int, unit: str = "days") -> KpiCardData:
            tot = float(curr_val)
            avg = round(curr_val / float(emp_count), 1)
            selected_count = tot if mode.lower() == "total" else avg

            if prev_val > 0:
                delta = round(abs(curr_val - prev_val) / float(prev_val) * 100, 1)
                trend = "up" if curr_val >= prev_val else "down"
            else:
                delta = 0.0
                trend = "neutral"

            return KpiCardData(
                title=title,
                total=tot,
                average=avg,
                count=selected_count,
                delta=delta,
                unit=unit,
                trend=trend,
            )

        return {
            "present": make_card("Present Days", c_pres, p_pres, "days"),
            "absent": make_card("Absent Days", c_abs, p_abs, "days"),
            "late": make_card("Late Arrivals", c_late, p_late, "arrivals"),
            "halfDay": make_card("Half Days", c_half, p_half, "days"),
        }

    # -------------------------------------------------------------------------
    # 6. GET /attendance/report/chart
    # -------------------------------------------------------------------------
    def get_report_chart(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        year: Optional[int] = None,
        department: Optional[str] = None,
    ) -> List[MonthlyChartBar]:
        org_uuid = _to_uuid(organization_id)
        curr_year = year or datetime.now(timezone.utc).year

        emp_query = db.query(EmployeePersonalInformationDb.employee_id).filter(
            EmployeePersonalInformationDb.organization_id == org_uuid
        )
        if department:
            emp_query = emp_query.join(
                EmployeeDepartmentInformationDb,
                EmployeeDepartmentInformationDb.employee_id == EmployeePersonalInformationDb.employee_id,
            ).filter(EmployeeDepartmentInformationDb.department == department)

        active_emp_ids = [r[0] for r in emp_query.all()]
        total_emps = len(active_emp_ids)

        records = (
            db.query(AttendanceRecordDb)
            .filter(
                AttendanceRecordDb.organization_id == org_uuid,
                AttendanceRecordDb.employee_id.in_(active_emp_ids) if active_emp_ids else True,
                func.extract("year", AttendanceRecordDb.date) == curr_year,
            )
            .all()
        )

        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        bars = []

        for m_idx, m_name in enumerate(month_names, 1):
            m_records = [r for r in records if r.date.month == m_idx]
            present_c = sum(1 for r in m_records if r.status == "Present")
            absent_c = sum(1 for r in m_records if r.status == "Absent")
            half_c = sum(1 for r in m_records if r.status == "Half Day")
            late_c = sum(1 for r in m_records if (r.late_minutes and r.late_minutes > 0) or r.status == "Late")

            bars.append(
                MonthlyChartBar(
                    month=m_name,
                    monthIndex=m_idx,
                    present=present_c,
                    absent=absent_c,
                    halfDay=half_c,
                    late=late_c,
                    totalEmployees=total_emps,
                )
            )

        return bars

    # -------------------------------------------------------------------------
    # 8. GET /attendance/employee/{id}/details
    # -------------------------------------------------------------------------
    def get_employee_details(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        employee_id: int,
        target_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        org_uuid = _to_uuid(organization_id)
        dt = target_date or datetime.now(timezone.utc).date()
        shift = self.get_effective_shift(db, org_uuid, employee_id)
        record = self.get_or_create_daily_record(db, org_uuid, employee_id, dt, shift)

        meta = self._get_employees_meta_map(db, org_uuid, [employee_id]).get(employee_id, {})

        punches = (
            db.query(AttendancePunchDb)
            .filter(AttendancePunchDb.attendance_record_id == record.id)
            .order_by(AttendancePunchDb.punch_time.asc())
            .all()
        )

        timeline = [
            TimelineEvent(
                id=p.id,
                time=p.punch_time,
                punchType=p.punch_type,
                note=p.note,
                location=p.location,
            )
            for p in punches
        ]

        month_records = (
            db.query(AttendanceRecordDb)
            .filter(
                AttendanceRecordDb.organization_id == org_uuid,
                AttendanceRecordDb.employee_id == employee_id,
                func.extract("year", AttendanceRecordDb.date) == dt.year,
                func.extract("month", AttendanceRecordDb.date) == dt.month,
            )
            .all()
        )

        pres_days = sum(1 for r in month_records if r.status == "Present")
        abs_days = sum(1 for r in month_records if r.status == "Absent")
        half_days = sum(1 for r in month_records if r.status == "Half Day")
        late_days = sum(1 for r in month_records if (r.late_minutes and r.late_minutes > 0))
        tot_prod = round(sum(float(r.production_hours or 0.0) for r in month_records), 2)
        tot_ot = round(sum(float(r.overtime_hours or 0.0) for r in month_records), 2)

        prod_hrs = float(record.production_hours) if record.production_hours else 0.0
        ind = "low" if prod_hrs < 8.0 else ("neutral" if prod_hrs <= 9.0 else "overtime")

        today_rec_resp = AttendanceRecordResponse(
            id=record.id,
            employeeId=record.employee_id,
            employeeName=meta.get("name"),
            employeeCode=meta.get("code"),
            department=meta.get("department"),
            designation=meta.get("designation"),
            avatar=meta.get("avatar"),
            date=record.date,
            checkIn=record.check_in,
            checkOut=record.check_out,
            totalWorkMinutes=record.total_work_minutes or 0,
            breakMinutes=record.break_minutes or 0,
            productionHours=prod_hrs,
            overtimeHours=float(record.overtime_hours or 0.0),
            lateMinutes=record.late_minutes or 0,
            earlyLeaveMinutes=record.early_leave_minutes or 0,
            status=record.status or "Absent",
            autoCheckedOut=bool(record.auto_checked_out),
            productionIndicator=ind,
            notes=record.notes,
        )

        return {
            "employee": {
                "id": employee_id,
                "name": meta.get("name"),
                "code": meta.get("code"),
                "department": meta.get("department"),
                "designation": meta.get("designation"),
                "avatar": meta.get("avatar"),
                "shift": shift.name if shift else "Standard Shift",
            },
            "kpis": {
                "presentDays": pres_days,
                "absentDays": abs_days,
                "halfDays": half_days,
                "lateDays": late_days,
                "totalProductionHours": tot_prod,
                "totalOvertimeHours": tot_ot,
            },
            "timeline": timeline,
            "todayRecord": today_rec_resp,
        }

    # -------------------------------------------------------------------------
    # Sync Monthly Stats
    # -------------------------------------------------------------------------
    def sync_monthly_stats(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        employee_id: int,
        year: int,
        month: int,
    ) -> AttendanceMonthlyStatsDb:
        org_uuid = _to_uuid(organization_id)
        records = (
            db.query(AttendanceRecordDb)
            .filter(
                AttendanceRecordDb.organization_id == org_uuid,
                AttendanceRecordDb.employee_id == employee_id,
                func.extract("year", AttendanceRecordDb.date) == year,
                func.extract("month", AttendanceRecordDb.date) == month,
            )
            .all()
        )

        present_c = sum(1 for r in records if r.status == "Present")
        absent_c = sum(1 for r in records if r.status == "Absent")
        half_c = sum(1 for r in records if r.status == "Half Day")
        late_c = sum(1 for r in records if (r.late_minutes and r.late_minutes > 0) or r.status == "Late")
        tot_prod = Decimal(f"{sum(float(r.production_hours or 0.0) for r in records):.2f}")
        tot_ot = Decimal(f"{sum(float(r.overtime_hours or 0.0) for r in records):.2f}")

        return CRUD_ATTENDANCE.upsert_monthly_stats(
            db=db,
            organization_id=org_uuid,
            employee_id=employee_id,
            year=year,
            month=month,
            present_days=present_c,
            absent_days=absent_c,
            half_days=half_c,
            late_days=late_c,
            total_production_hours=tot_prod,
            total_overtime_hours=tot_ot,
            working_days=len(records),
        )

    # -------------------------------------------------------------------------
    # 10. GET /attendance/export
    # -------------------------------------------------------------------------
    def export_attendance_csv(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        records: List[AttendanceRecordResponse],
    ) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Employee ID",
            "Employee Code",
            "Employee Name",
            "Department",
            "Date",
            "Check In",
            "Check Out",
            "Total Work Minutes",
            "Break Minutes",
            "Production Hours",
            "Overtime Hours",
            "Late Minutes",
            "Status",
            "Auto Checked Out",
        ])

        for r in records:
            writer.writerow([
                r.employeeId,
                r.employeeCode or "",
                r.employeeName or "",
                r.department or "",
                r.date.isoformat(),
                r.checkIn.isoformat() if r.checkIn else "",
                r.checkOut.isoformat() if r.checkOut else "",
                r.totalWorkMinutes,
                r.breakMinutes,
                r.productionHours,
                r.overtimeHours,
                r.lateMinutes,
                r.status,
                r.autoCheckedOut,
            ])

        return output.getvalue()


ATTENDANCE_SERVICE = AttendanceService()
