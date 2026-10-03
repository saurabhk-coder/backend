import uuid
from datetime import datetime, time, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.calendar_setting import CalendarSettingDb, CalendarWeekendRuleDb
from ..schemas.calendar_setting import (
    DEFAULT_DAYS_OF_WEEK,
    CalendarSettingCreate,
    CalendarSettingData,
    CalendarSettingUpdate,
    FiscalYearConfig,
    LeaveYearConfig,
    MinimumHoursConfig,
    WeekendRule,
    WorkScheduleConfig,
    normalize_weekend_definition,
    serialize_weekend_definition_for_db,
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


def sync_weekend_rules(
    db: Session,
    calendar_setting_id: uuid.UUID,
    weekend_def_dict: Dict[str, Any],
) -> None:
    """
    Synchronize the 7 records in hrms.calendar_weekend_rules for SQL joins / attendance calculations.
    """
    normalized = normalize_weekend_definition(weekend_def_dict)
    existing_rules = {
        rule.day_of_week: rule
        for rule in db.query(CalendarWeekendRuleDb)
        .filter(CalendarWeekendRuleDb.calendar_setting_id == calendar_setting_id)
        .all()
    }

    for day in DEFAULT_DAYS_OF_WEEK:
        rule_obj = normalized.get(day, WeekendRule())
        rule_dict = rule_obj.model_dump(by_alias=True)
        if day in existing_rules:
            db_rule = existing_rules[day]
            db_rule.week_1st = rule_dict.get("1st", False)
            db_rule.week_2nd = rule_dict.get("2nd", False)
            db_rule.week_3rd = rule_dict.get("3rd", False)
            db_rule.week_4th = rule_dict.get("4th", False)
            db_rule.week_5th = rule_dict.get("5th", False)
            db_rule.week_last = rule_dict.get("last", False)
            db_rule.week_alt = rule_dict.get("alt", False)
        else:
            db_rule = CalendarWeekendRuleDb(
                id=uuid.uuid4(),
                calendar_setting_id=calendar_setting_id,
                day_of_week=day,
                week_1st=rule_dict.get("1st", False),
                week_2nd=rule_dict.get("2nd", False),
                week_3rd=rule_dict.get("3rd", False),
                week_4th=rule_dict.get("4th", False),
                week_5th=rule_dict.get("5th", False),
                week_last=rule_dict.get("last", False),
                week_alt=rule_dict.get("alt", False),
            )
            db.add(db_rule)


class CRUDCalendarSetting:
    def to_schema(self, db_obj: CalendarSettingDb) -> CalendarSettingData:
        normalized_weekends = normalize_weekend_definition(db_obj.weekend_definition)
        return CalendarSettingData(
            id=db_obj.id,
            organizationId=db_obj.organization_id,
            location=db_obj.location,
            isDefault=db_obj.is_default,
            fiscalYear=FiscalYearConfig(
                sameAsCalendar=db_obj.fiscal_year_same_as_calendar,
                startMonth=db_obj.fiscal_year_start_month,
                endMonth=db_obj.fiscal_year_end_month,
            ),
            leaveYear=LeaveYearConfig(
                sameAsCalendar=db_obj.leave_year_same_as_calendar,
                startMonth=db_obj.leave_year_start_month,
                endMonth=db_obj.leave_year_end_month,
            ),
            workSchedule=WorkScheduleConfig(
                maxWorkingHoursPerDay=db_obj.max_working_hours_per_day or "09:00",
                weekStartsOn=db_obj.week_starts_on or "Monday",
                shiftStartTime=_format_time(db_obj.shift_start_time, "09:00"),
                shiftEndTime=_format_time(db_obj.shift_end_time, "18:00"),
            ),
            minimumHours=MinimumHoursConfig(
                fullDay=db_obj.full_day_hours or "08:00",
                fullDayTolerance=db_obj.full_day_tolerance or "00:00",
                halfDay=db_obj.half_day_hours or "04:00",
                halfDayTolerance=db_obj.half_day_tolerance or "00:00",
            ),
            weekendDefinition=normalized_weekends,
            createdAt=db_obj.created_at,
            updatedAt=db_obj.updated_at,
        )

    def get_by_id(
        self,
        db: Session,
        *,
        id: Union[uuid.UUID, str],
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> Optional[CalendarSettingDb]:
        try:
            setting_uuid = _to_uuid(id)
            query = db.query(CalendarSettingDb).filter(CalendarSettingDb.id == setting_uuid)
            if organization_id:
                query = query.filter(CalendarSettingDb.organization_id == _to_uuid(organization_id))
            return query.first()
        except (ValueError, TypeError):
            return None

    def get_by_location(
        self,
        db: Session,
        *,
        location: str,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> Optional[CalendarSettingDb]:
        clean_loc = location.strip()
        query = db.query(CalendarSettingDb).filter(
            func.lower(CalendarSettingDb.location) == clean_loc.lower()
        )
        if organization_id:
            try:
                query = query.filter(CalendarSettingDb.organization_id == _to_uuid(organization_id))
            except (ValueError, TypeError):
                return None
        return query.first()

    def get_default(
        self,
        db: Session,
        *,
        organization_id: Union[uuid.UUID, str],
    ) -> Optional[CalendarSettingDb]:
        try:
            org_uuid = _to_uuid(organization_id)
            return (
                db.query(CalendarSettingDb)
                .filter(
                    CalendarSettingDb.organization_id == org_uuid,
                    CalendarSettingDb.is_default == True,
                )
                .first()
            )
        except (ValueError, TypeError):
            return None

    def get_by_id_or_location(
        self,
        db: Session,
        *,
        identifier: Union[uuid.UUID, str],
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> Optional[CalendarSettingDb]:
        id_str = str(identifier).strip()
        # 1. Try UUID lookup
        try:
            parsed_uuid = _to_uuid(id_str)
            found = self.get_by_id(db, id=parsed_uuid, organization_id=organization_id)
            if found:
                return found
        except (ValueError, TypeError):
            pass

        # 2. Check if keyword 'default'
        if id_str.lower() == "default" and organization_id:
            found_default = self.get_default(db, organization_id=organization_id)
            if found_default:
                return found_default

        # 3. Lookup by location
        return self.get_by_location(db, location=id_str, organization_id=organization_id)

    def get_multi(
        self,
        db: Session,
        *,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
        location: Optional[str] = None,
        is_default: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CalendarSettingDb]:
        query = db.query(CalendarSettingDb)
        if organization_id:
            try:
                query = query.filter(CalendarSettingDb.organization_id == _to_uuid(organization_id))
            except (ValueError, TypeError):
                return []
        if location:
            query = query.filter(CalendarSettingDb.location.ilike(f"%{location.strip()}%"))
        if is_default is not None:
            query = query.filter(CalendarSettingDb.is_default == is_default)

        return (
            query.order_by(CalendarSettingDb.is_default.desc(), CalendarSettingDb.location.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count(
        self,
        db: Session,
        *,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> int:
        query = db.query(CalendarSettingDb)
        if organization_id:
            try:
                query = query.filter(CalendarSettingDb.organization_id == _to_uuid(organization_id))
            except (ValueError, TypeError):
                return 0
        return query.count()

    def create_or_upsert(
        self,
        db: Session,
        *,
        organization_id: Union[uuid.UUID, str],
        obj_in: CalendarSettingCreate,
    ) -> Tuple[CalendarSettingDb, bool]:
        """
        Creates or upserts calendar setting. Returns (setting_db_obj, is_new_record).
        """
        org_uuid = _to_uuid(organization_id)
        now = datetime.now(timezone.utc)
        location = obj_in.location.strip()

        # Check if setting already exists for this org and location
        db_obj = self.get_by_location(db, location=location, organization_id=org_uuid)
        is_new = db_obj is None

        # Count existing settings for org
        existing_count = self.count(db, organization_id=org_uuid)

        # Determine default flag:
        # If this is the first setting for the org, default to True unless explicitly False
        is_def = obj_in.isDefault
        if is_new and existing_count == 0:
            is_def = True
        elif is_def is None:
            is_def = False

        if is_def:
            # Clear existing default flags for this organization
            db.query(CalendarSettingDb).filter(
                CalendarSettingDb.organization_id == org_uuid,
                CalendarSettingDb.is_default == True,
            ).update({"is_default": False})

        # Normalize weekend definition
        normalized_weekends = normalize_weekend_definition(obj_in.weekendDefinition)
        db_weekend_dict = serialize_weekend_definition_for_db(normalized_weekends)

        # Fiscal year
        fiscal_same = obj_in.fiscalYear.sameAsCalendar if obj_in.fiscalYear else True
        fiscal_start = obj_in.fiscalYear.startMonth if obj_in.fiscalYear else "January"
        fiscal_end = obj_in.fiscalYear.endMonth if obj_in.fiscalYear else "December"

        # Leave year
        leave_same = obj_in.leaveYear.sameAsCalendar if obj_in.leaveYear else True
        leave_start = obj_in.leaveYear.startMonth if obj_in.leaveYear else "January"
        leave_end = obj_in.leaveYear.endMonth if obj_in.leaveYear else "December"

        # Work schedule
        max_work_hours = obj_in.workSchedule.maxWorkingHoursPerDay if obj_in.workSchedule else "09:00"
        week_start = obj_in.workSchedule.weekStartsOn if obj_in.workSchedule else "Monday"
        shift_start = _parse_time(
            obj_in.workSchedule.shiftStartTime if obj_in.workSchedule else None,
            default=time(9, 0),
        )
        shift_end = _parse_time(
            obj_in.workSchedule.shiftEndTime if obj_in.workSchedule else None,
            default=time(18, 0),
        )

        # Minimum hours
        full_day = obj_in.minimumHours.fullDay if obj_in.minimumHours else "08:00"
        full_tol = obj_in.minimumHours.fullDayTolerance if obj_in.minimumHours else "00:00"
        half_day = obj_in.minimumHours.halfDay if obj_in.minimumHours else "04:00"
        half_tol = obj_in.minimumHours.halfDayTolerance if obj_in.minimumHours else "00:00"

        if is_new:
            db_obj = CalendarSettingDb(
                id=uuid.uuid4(),
                organization_id=org_uuid,
                location=location,
                is_default=bool(is_def),
                fiscal_year_same_as_calendar=fiscal_same,
                fiscal_year_start_month=fiscal_start,
                fiscal_year_end_month=fiscal_end,
                leave_year_same_as_calendar=leave_same,
                leave_year_start_month=leave_start,
                leave_year_end_month=leave_end,
                max_working_hours_per_day=max_work_hours,
                week_starts_on=week_start,
                shift_start_time=shift_start,
                shift_end_time=shift_end,
                full_day_hours=full_day,
                full_day_tolerance=full_tol,
                half_day_hours=half_day,
                half_day_tolerance=half_tol,
                weekend_definition=db_weekend_dict,
                created_at=now,
                updated_at=now,
            )
            db.add(db_obj)
            db.flush()
        else:
            db_obj.location = location
            if is_def is not None:
                db_obj.is_default = bool(is_def)
            if obj_in.fiscalYear is not None:
                db_obj.fiscal_year_same_as_calendar = fiscal_same
                db_obj.fiscal_year_start_month = fiscal_start
                db_obj.fiscal_year_end_month = fiscal_end
            if obj_in.leaveYear is not None:
                db_obj.leave_year_same_as_calendar = leave_same
                db_obj.leave_year_start_month = leave_start
                db_obj.leave_year_end_month = leave_end
            if obj_in.workSchedule is not None:
                db_obj.max_working_hours_per_day = max_work_hours
                db_obj.week_starts_on = week_start
                db_obj.shift_start_time = shift_start
                db_obj.shift_end_time = shift_end
            if obj_in.minimumHours is not None:
                db_obj.full_day_hours = full_day
                db_obj.full_day_tolerance = full_tol
                db_obj.half_day_hours = half_day
                db_obj.half_day_tolerance = half_tol
            if obj_in.weekendDefinition is not None:
                db_obj.weekend_definition = db_weekend_dict
            db_obj.updated_at = now
            db.flush()

        # Synchronize normalized relational weekend rules
        sync_weekend_rules(db, db_obj.id, db_weekend_dict)

        db.commit()
        db.refresh(db_obj)
        return db_obj, is_new

    def update(
        self,
        db: Session,
        *,
        db_obj: CalendarSettingDb,
        obj_in: CalendarSettingUpdate,
    ) -> CalendarSettingDb:
        now = datetime.now(timezone.utc)

        if obj_in.location is not None:
            db_obj.location = obj_in.location.strip()

        if obj_in.isDefault is not None:
            if obj_in.isDefault:
                db.query(CalendarSettingDb).filter(
                    CalendarSettingDb.organization_id == db_obj.organization_id,
                    CalendarSettingDb.id != db_obj.id,
                    CalendarSettingDb.is_default == True,
                ).update({"is_default": False})
            db_obj.is_default = obj_in.isDefault

        if obj_in.fiscalYear is not None:
            db_obj.fiscal_year_same_as_calendar = obj_in.fiscalYear.sameAsCalendar
            db_obj.fiscal_year_start_month = obj_in.fiscalYear.startMonth
            db_obj.fiscal_year_end_month = obj_in.fiscalYear.endMonth

        if obj_in.leaveYear is not None:
            db_obj.leave_year_same_as_calendar = obj_in.leaveYear.sameAsCalendar
            db_obj.leave_year_start_month = obj_in.leaveYear.startMonth
            db_obj.leave_year_end_month = obj_in.leaveYear.endMonth

        if obj_in.workSchedule is not None:
            db_obj.max_working_hours_per_day = obj_in.workSchedule.maxWorkingHoursPerDay
            db_obj.week_starts_on = obj_in.workSchedule.weekStartsOn
            if obj_in.workSchedule.shiftStartTime:
                db_obj.shift_start_time = _parse_time(
                    obj_in.workSchedule.shiftStartTime, default=db_obj.shift_start_time
                )
            if obj_in.workSchedule.shiftEndTime:
                db_obj.shift_end_time = _parse_time(
                    obj_in.workSchedule.shiftEndTime, default=db_obj.shift_end_time
                )

        if obj_in.minimumHours is not None:
            db_obj.full_day_hours = obj_in.minimumHours.fullDay
            db_obj.full_day_tolerance = obj_in.minimumHours.fullDayTolerance
            db_obj.half_day_hours = obj_in.minimumHours.halfDay
            db_obj.half_day_tolerance = obj_in.minimumHours.halfDayTolerance

        if obj_in.weekendDefinition is not None:
            normalized_weekends = normalize_weekend_definition(obj_in.weekendDefinition)
            db_weekend_dict = serialize_weekend_definition_for_db(normalized_weekends)
            db_obj.weekend_definition = db_weekend_dict
            sync_weekend_rules(db, db_obj.id, db_weekend_dict)

        db_obj.updated_at = now
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(
        self,
        db: Session,
        *,
        db_obj: CalendarSettingDb,
    ) -> CalendarSettingDb:
        org_id = db_obj.organization_id
        was_default = db_obj.is_default

        db.delete(db_obj)
        db.flush()

        # If deleted setting was default, fallback to another calendar setting for the organization
        if was_default:
            next_default = (
                db.query(CalendarSettingDb)
                .filter(CalendarSettingDb.organization_id == org_id)
                .order_by(CalendarSettingDb.created_at.asc())
                .first()
            )
            if next_default:
                next_default.is_default = True

        db.commit()
        return db_obj


CRUD_CALENDAR_SETTING = CRUDCalendarSetting()
