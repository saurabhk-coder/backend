import uuid
from datetime import datetime, time, timezone
from typing import Any, List, Optional, Tuple, Union
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..models.shift import ShiftDb, ShiftGracePeriodDb, ShiftReminderDb
from ..schemas.shift import (
    GracePeriodPolicy,
    MinimumHours,
    ReminderDetail,
    ShiftCreate,
    ShiftReminder,
    ShiftResponse,
    ShiftUpdate,
)


def _to_uuid(val: Union[uuid.UUID, str]) -> uuid.UUID:
    if isinstance(val, uuid.UUID):
        return val
    return uuid.UUID(str(val).strip())


def _format_time(val: Any, default: str = "09:00") -> str:
    if val is None:
        return default
    if isinstance(val, str):
        val = val.strip()
        return val[:5] if len(val) >= 5 else val
    if hasattr(val, "strftime"):
        return val.strftime("%H:%M")
    return str(val)


def _parse_time(val: Any, default: Optional[time] = None) -> Optional[time]:
    if val is None:
        return default
    if isinstance(val, time):
        return val
    if isinstance(val, str):
        val = val.strip()
        parts = val.split(":")
        if len(parts) >= 2:
            try:
                hour = int(parts[0])
                minute = int(parts[1])
                second = int(parts[2]) if len(parts) > 2 else 0
                return time(hour, minute, second)
            except (ValueError, TypeError):
                return default
    return default


def _calculate_duration(start_t: time, end_t: time) -> str:
    """Calculate duration between start and end time in HH:MM format."""
    start_minutes = start_t.hour * 60 + start_t.minute
    end_minutes = end_t.hour * 60 + end_t.minute
    if end_minutes < start_minutes:
        # Crosses midnight
        diff_minutes = (24 * 60 - start_minutes) + end_minutes
    else:
        diff_minutes = end_minutes - start_minutes
    hours = diff_minutes // 60
    mins = diff_minutes % 60
    return f"{hours:02d}:{mins:02d}"


class CRUDShift:
    def to_schema(self, db_obj: ShiftDb) -> ShiftResponse:
        # Grace period
        if db_obj.grace_period:
            grace = GracePeriodPolicy(
                enabled=db_obj.grace_period.is_enabled,
                lateCheckInMinutes=db_obj.grace_period.late_check_in_minutes,
                earlyCheckOutMinutes=db_obj.grace_period.early_check_out_minutes,
            )
        else:
            grace = GracePeriodPolicy()

        # Shift reminder
        if db_obj.reminder:
            reminder = ShiftReminder(
                checkIn=ReminderDetail(
                    enabled=db_obj.reminder.check_in_enabled,
                    beforeTime=db_obj.reminder.check_in_before or "00:00",
                    afterTime=db_obj.reminder.check_in_after or "00:00",
                ),
                checkOut=ReminderDetail(
                    enabled=db_obj.reminder.check_out_enabled,
                    beforeTime=db_obj.reminder.check_out_before or "00:00",
                    afterTime=db_obj.reminder.check_out_after or "00:00",
                ),
            )
        else:
            reminder = ShiftReminder()

        # Minimum hours
        min_hours = MinimumHours(
            fullDay=db_obj.full_day_hours or "08:00",
            fullDayTolerance=db_obj.full_day_tolerance or "00:00",
            halfDay=db_obj.half_day_hours or "04:00",
            halfDayTolerance=db_obj.half_day_tolerance or "00:00",
        )

        return ShiftResponse(
            id=db_obj.id,
            name=db_obj.name,
            startTime=_format_time(db_obj.start_time, "09:00"),
            endTime=_format_time(db_obj.end_time, "18:00"),
            shiftDuration=db_obj.shift_duration or "09:00",
            startDate=db_obj.start_date,
            endDate=db_obj.end_date,
            peopleRequired=db_obj.people_required,
            color=db_obj.color or "#F05A28",
            workArea=db_obj.work_area,
            department=db_obj.department,
            location=db_obj.location,
            payCalculationType=db_obj.pay_calculation_type or "per_day",
            minimumHours=min_hours,
            recurrencePattern=db_obj.recurrence_pattern or "daily",
            weeklyDays=db_obj.weekly_working_days or ["Mon", "Tue", "Wed", "Thu", "Fri"],
            calendarWeekendPolicy=db_obj.calendar_weekend_policy or "calendar",
            gracePeriodPolicy=grace,
            shiftReminder=reminder,
            isActive=db_obj.is_active,
            createdAt=db_obj.created_at,
            updatedAt=db_obj.updated_at,
            organizationId=db_obj.organization_id,
        )

    def get(
        self,
        db: Session,
        *,
        id: Union[uuid.UUID, str],
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> Optional[ShiftDb]:
        try:
            shift_uuid = _to_uuid(id)
            query = db.query(ShiftDb).filter(ShiftDb.id == shift_uuid)
            if organization_id:
                query = query.filter(ShiftDb.organization_id == _to_uuid(organization_id))
            return query.first()
        except (ValueError, TypeError):
            return None

    def get_multi(
        self,
        db: Session,
        *,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
        search: Optional[str] = None,
        department: Optional[str] = None,
        location: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[ShiftDb], int]:
        query = db.query(ShiftDb)

        if organization_id:
            try:
                query = query.filter(ShiftDb.organization_id == _to_uuid(organization_id))
            except (ValueError, TypeError):
                return [], 0

        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    ShiftDb.name.ilike(search_pattern),
                    ShiftDb.department.ilike(search_pattern),
                    ShiftDb.location.ilike(search_pattern),
                    ShiftDb.work_area.ilike(search_pattern),
                )
            )

        if department:
            query = query.filter(ShiftDb.department.ilike(f"%{department.strip()}%"))

        if location:
            query = query.filter(ShiftDb.location.ilike(f"%{location.strip()}%"))

        if is_active is not None:
            query = query.filter(ShiftDb.is_active == is_active)

        total = query.count()
        shifts = (
            query.order_by(ShiftDb.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return shifts, total

    def create(
        self,
        db: Session,
        *,
        organization_id: Union[uuid.UUID, str],
        obj_in: ShiftCreate,
    ) -> ShiftDb:
        org_uuid = _to_uuid(organization_id)
        now = datetime.now(timezone.utc)
        start_t = _parse_time(obj_in.startTime, time(9, 0))
        end_t = _parse_time(obj_in.endTime, time(18, 0))
        duration = obj_in.shiftDuration or _calculate_duration(start_t, end_t)

        min_hours = obj_in.minimumHours or MinimumHours()

        db_shift = ShiftDb(
            id=uuid.uuid4(),
            organization_id=org_uuid,
            name=obj_in.name.strip(),
            start_time=start_t,
            end_time=end_t,
            shift_duration=duration,
            start_date=obj_in.startDate,
            end_date=obj_in.endDate,
            people_required=obj_in.peopleRequired,
            color=obj_in.color or "#F05A28",
            work_area=obj_in.workArea,
            department=obj_in.department,
            location=obj_in.location,
            pay_calculation_type=obj_in.payCalculationType or "per_day",
            full_day_hours=min_hours.fullDay or "08:00",
            full_day_tolerance=min_hours.fullDayTolerance or "00:00",
            half_day_hours=min_hours.halfDay or "04:00",
            half_day_tolerance=min_hours.halfDayTolerance or "00:00",
            recurrence_pattern=obj_in.recurrencePattern or "daily",
            weekly_working_days=obj_in.weeklyDays or ["Mon", "Tue", "Wed", "Thu", "Fri"],
            calendar_weekend_policy=obj_in.calendarWeekendPolicy or "calendar",
            is_active=True if obj_in.isActive is None else obj_in.isActive,
            created_at=now,
            updated_at=now,
        )
        db.add(db_shift)
        db.flush()

        # Grace period
        gp_in = obj_in.gracePeriodPolicy or GracePeriodPolicy()
        db_grace = ShiftGracePeriodDb(
            id=uuid.uuid4(),
            shift_id=db_shift.id,
            is_enabled=gp_in.enabled,
            late_check_in_minutes=gp_in.lateCheckInMinutes,
            early_check_out_minutes=gp_in.earlyCheckOutMinutes,
        )
        db.add(db_grace)

        # Reminder
        rem_in = obj_in.shiftReminder or ShiftReminder()
        db_rem = ShiftReminderDb(
            id=uuid.uuid4(),
            shift_id=db_shift.id,
            check_in_enabled=rem_in.checkIn.enabled,
            check_in_before=rem_in.checkIn.beforeTime,
            check_in_after=rem_in.checkIn.afterTime,
            check_out_enabled=rem_in.checkOut.enabled,
            check_out_before=rem_in.checkOut.beforeTime,
            check_out_after=rem_in.checkOut.afterTime,
        )
        db.add(db_rem)

        db.commit()
        db.refresh(db_shift)
        return db_shift

    def update(
        self,
        db: Session,
        *,
        db_obj: ShiftDb,
        obj_in: ShiftUpdate,
    ) -> ShiftDb:
        now = datetime.now(timezone.utc)

        if obj_in.name is not None:
            db_obj.name = obj_in.name.strip()
        if obj_in.startTime is not None:
            db_obj.start_time = _parse_time(obj_in.startTime, db_obj.start_time)
        if obj_in.endTime is not None:
            db_obj.end_time = _parse_time(obj_in.endTime, db_obj.end_time)

        if obj_in.shiftDuration is not None:
            db_obj.shift_duration = obj_in.shiftDuration
        elif obj_in.startTime is not None or obj_in.endTime is not None:
            db_obj.shift_duration = _calculate_duration(db_obj.start_time, db_obj.end_time)

        if obj_in.startDate is not None:
            db_obj.start_date = obj_in.startDate
        if obj_in.endDate is not None:
            db_obj.end_date = obj_in.endDate
        if obj_in.peopleRequired is not None:
            db_obj.people_required = obj_in.peopleRequired
        if obj_in.color is not None:
            db_obj.color = obj_in.color
        if obj_in.workArea is not None:
            db_obj.work_area = obj_in.workArea
        if obj_in.department is not None:
            db_obj.department = obj_in.department
        if obj_in.location is not None:
            db_obj.location = obj_in.location
        if obj_in.payCalculationType is not None:
            db_obj.pay_calculation_type = obj_in.payCalculationType

        if obj_in.minimumHours is not None:
            if obj_in.minimumHours.fullDay is not None:
                db_obj.full_day_hours = obj_in.minimumHours.fullDay
            if obj_in.minimumHours.fullDayTolerance is not None:
                db_obj.full_day_tolerance = obj_in.minimumHours.fullDayTolerance
            if obj_in.minimumHours.halfDay is not None:
                db_obj.half_day_hours = obj_in.minimumHours.halfDay
            if obj_in.minimumHours.halfDayTolerance is not None:
                db_obj.half_day_tolerance = obj_in.minimumHours.halfDayTolerance

        if obj_in.recurrencePattern is not None:
            db_obj.recurrence_pattern = obj_in.recurrencePattern
        if obj_in.weeklyDays is not None:
            db_obj.weekly_working_days = obj_in.weeklyDays
        if obj_in.calendarWeekendPolicy is not None:
            db_obj.calendar_weekend_policy = obj_in.calendarWeekendPolicy
        if obj_in.isActive is not None:
            db_obj.is_active = obj_in.isActive

        db_obj.updated_at = now

        # Update grace period
        if obj_in.gracePeriodPolicy is not None:
            gp = db_obj.grace_period
            if not gp:
                gp = ShiftGracePeriodDb(id=uuid.uuid4(), shift_id=db_obj.id)
                db.add(gp)
            gp.is_enabled = obj_in.gracePeriodPolicy.enabled
            gp.late_check_in_minutes = obj_in.gracePeriodPolicy.lateCheckInMinutes
            gp.early_check_out_minutes = obj_in.gracePeriodPolicy.earlyCheckOutMinutes

        # Update reminders
        if obj_in.shiftReminder is not None:
            rem = db_obj.reminder
            if not rem:
                rem = ShiftReminderDb(id=uuid.uuid4(), shift_id=db_obj.id)
                db.add(rem)
            rem.check_in_enabled = obj_in.shiftReminder.checkIn.enabled
            rem.check_in_before = obj_in.shiftReminder.checkIn.beforeTime
            rem.check_in_after = obj_in.shiftReminder.checkIn.afterTime
            rem.check_out_enabled = obj_in.shiftReminder.checkOut.enabled
            rem.check_out_before = obj_in.shiftReminder.checkOut.beforeTime
            rem.check_out_after = obj_in.shiftReminder.checkOut.afterTime

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, db_obj: ShiftDb) -> ShiftDb:
        db.delete(db_obj)
        db.commit()
        return db_obj


CRUD_SHIFT = CRUDShift()
