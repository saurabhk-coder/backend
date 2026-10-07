import math
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.attendance import (
    AttendanceAuditLogDb,
    AttendanceMonthlyStatsDb,
    AttendancePunchDb,
    AttendanceRecordDb,
)
from ..schemas.attendance import (
    AttendancePunchCreate,
    AttendanceRecordCreate,
    AttendanceRecordUpdate,
)


def _to_uuid(val: Union[uuid.UUID, str]) -> uuid.UUID:
    if isinstance(val, uuid.UUID):
        return val
    return uuid.UUID(str(val).strip())


class CRUDAttendance:
    def get(
        self,
        db: Session,
        record_id: Union[uuid.UUID, str],
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> Optional[AttendanceRecordDb]:
        rec_uuid = _to_uuid(record_id)
        query = db.query(AttendanceRecordDb).filter(AttendanceRecordDb.id == rec_uuid)
        if organization_id is not None:
            query = query.filter(AttendanceRecordDb.organization_id == _to_uuid(organization_id))
        return query.first()

    def get_by_employee_and_date(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        employee_id: int,
        record_date: date,
    ) -> Optional[AttendanceRecordDb]:
        return (
            db.query(AttendanceRecordDb)
            .filter(
                AttendanceRecordDb.organization_id == _to_uuid(organization_id),
                AttendanceRecordDb.employee_id == employee_id,
                AttendanceRecordDb.date == record_date,
            )
            .first()
        )

    def get_multi(
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
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "date",
        sort_order: str = "desc",
    ) -> Tuple[List[AttendanceRecordDb], int]:
        query = db.query(AttendanceRecordDb).filter(
            AttendanceRecordDb.organization_id == _to_uuid(organization_id)
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

        total = query.count()

        sort_col = getattr(AttendanceRecordDb, sort_by, AttendanceRecordDb.date)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        records = query.offset((page - 1) * page_size).limit(page_size).all()
        return records, total

    def create(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        obj_in: AttendanceRecordCreate,
    ) -> AttendanceRecordDb:
        record = AttendanceRecordDb(
            organization_id=_to_uuid(organization_id),
            employee_id=obj_in.employeeId,
            date=obj_in.date,
            shift_id=_to_uuid(obj_in.shiftId) if obj_in.shiftId else None,
            check_in=obj_in.checkIn,
            check_out=obj_in.checkOut,
            status=obj_in.status or "Present",
            notes=obj_in.notes,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def update(
        self,
        db: Session,
        record: AttendanceRecordDb,
        obj_in: AttendanceRecordUpdate,
    ) -> AttendanceRecordDb:
        if obj_in.checkIn is not None:
            record.check_in = obj_in.checkIn
        if obj_in.checkOut is not None:
            record.check_out = obj_in.checkOut
        if obj_in.status is not None:
            record.status = obj_in.status
        if obj_in.notes is not None:
            record.notes = obj_in.notes

        record.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(record)
        return record

    def remove(self, db: Session, record: AttendanceRecordDb) -> None:
        db.delete(record)
        db.commit()

    # -------------------------------------------------------------------------
    # Punches
    # -------------------------------------------------------------------------
    def get_punches(
        self,
        db: Session,
        record_id: Union[uuid.UUID, str],
    ) -> List[AttendancePunchDb]:
        return (
            db.query(AttendancePunchDb)
            .filter(AttendancePunchDb.attendance_record_id == _to_uuid(record_id))
            .order_by(AttendancePunchDb.punch_time.asc())
            .all()
        )

    def create_punch(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        employee_id: int,
        record_id: Union[uuid.UUID, str],
        punch_type: str,
        punch_time: Optional[datetime] = None,
        location: Optional[str] = None,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
        note: Optional[str] = None,
    ) -> AttendancePunchDb:
        punch = AttendancePunchDb(
            organization_id=_to_uuid(organization_id),
            attendance_record_id=_to_uuid(record_id),
            employee_id=employee_id,
            punch_time=punch_time or datetime.now(timezone.utc),
            punch_type=punch_type.upper(),
            location=location,
            device_info=device_info,
            ip_address=ip_address,
            note=note,
        )
        db.add(punch)
        db.commit()
        db.refresh(punch)
        return punch

    def get_punch(
        self,
        db: Session,
        punch_id: Union[uuid.UUID, str],
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> Optional[AttendancePunchDb]:
        p_uuid = _to_uuid(punch_id)
        query = db.query(AttendancePunchDb).filter(AttendancePunchDb.id == p_uuid)
        if organization_id is not None:
            query = query.filter(AttendancePunchDb.organization_id == _to_uuid(organization_id))
        return query.first()

    def delete_punch(self, db: Session, punch: AttendancePunchDb) -> None:
        db.delete(punch)
        db.commit()

    # -------------------------------------------------------------------------
    # Audit Logs
    # -------------------------------------------------------------------------
    def create_audit_log(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        employee_id: int,
        action: str,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        attendance_record_id: Optional[Union[uuid.UUID, str]] = None,
        reason: Optional[str] = None,
        changed_by: str = "system",
    ) -> AttendanceAuditLogDb:
        log = AttendanceAuditLogDb(
            organization_id=_to_uuid(organization_id),
            attendance_record_id=_to_uuid(attendance_record_id) if attendance_record_id else None,
            employee_id=employee_id,
            action=action,
            old_values=old_values,
            new_values=new_values,
            reason=reason,
            changed_by=changed_by,
            changed_at=datetime.now(timezone.utc),
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def get_audit_logs(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        attendance_record_id: Optional[Union[uuid.UUID, str]] = None,
        employee_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[AttendanceAuditLogDb], int]:
        query = db.query(AttendanceAuditLogDb).filter(
            AttendanceAuditLogDb.organization_id == _to_uuid(organization_id)
        )
        if attendance_record_id:
            query = query.filter(
                AttendanceAuditLogDb.attendance_record_id == _to_uuid(attendance_record_id)
            )
        if employee_id:
            query = query.filter(AttendanceAuditLogDb.employee_id == employee_id)

        total = query.count()
        logs = (
            query.order_by(AttendanceAuditLogDb.changed_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return logs, total

    # -------------------------------------------------------------------------
    # Monthly Stats
    # -------------------------------------------------------------------------
    def get_monthly_stats(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        employee_id: int,
        year: int,
        month: int,
    ) -> Optional[AttendanceMonthlyStatsDb]:
        return (
            db.query(AttendanceMonthlyStatsDb)
            .filter(
                AttendanceMonthlyStatsDb.organization_id == _to_uuid(organization_id),
                AttendanceMonthlyStatsDb.employee_id == employee_id,
                AttendanceMonthlyStatsDb.year == year,
                AttendanceMonthlyStatsDb.month == month,
            )
            .first()
        )

    def upsert_monthly_stats(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        employee_id: int,
        year: int,
        month: int,
        **kwargs: Any,
    ) -> AttendanceMonthlyStatsDb:
        stat = self.get_monthly_stats(db, organization_id, employee_id, year, month)
        if not stat:
            stat = AttendanceMonthlyStatsDb(
                organization_id=_to_uuid(organization_id),
                employee_id=employee_id,
                year=year,
                month=month,
            )
            db.add(stat)

        for key, val in kwargs.items():
            if hasattr(stat, key):
                setattr(stat, key, val)

        stat.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(stat)
        return stat


CRUD_ATTENDANCE = CRUDAttendance()
