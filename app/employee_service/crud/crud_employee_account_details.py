from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..models.employee_account_details import EmployeeAccountDetailsDb
from ..schemas.employee_account_details import (
    EmployeeAccountDetailsCreate,
    EmployeeAccountDetailsUpdate,
)


class CRUDEmployeeAccountDetails:
    def get(self, db: Session, employee_id: int) -> Optional[EmployeeAccountDetailsDb]:
        try:
            return (
                db.query(EmployeeAccountDetailsDb)
                .filter(EmployeeAccountDetailsDb.employee_id == employee_id)
                .first()
            )
        except (ValueError, TypeError):
            return None

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> List[EmployeeAccountDetailsDb]:
        query = db.query(EmployeeAccountDetailsDb)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    EmployeeAccountDetailsDb.bank_name.ilike(pattern),
                    EmployeeAccountDetailsDb.ifsc_code.ilike(pattern),
                    EmployeeAccountDetailsDb.account_number.ilike(pattern),
                )
            )
        return (
            query.order_by(EmployeeAccountDetailsDb.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count(self, db: Session, *, search: Optional[str] = None) -> int:
        query = db.query(func.count(EmployeeAccountDetailsDb.employee_id))
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    EmployeeAccountDetailsDb.bank_name.ilike(pattern),
                    EmployeeAccountDetailsDb.ifsc_code.ilike(pattern),
                    EmployeeAccountDetailsDb.account_number.ilike(pattern),
                )
            )
        return query.scalar() or 0

    def create(
        self, db: Session, *, obj_in: EmployeeAccountDetailsCreate
    ) -> EmployeeAccountDetailsDb:
        now = datetime.now(timezone.utc)
        data = obj_in.model_dump()
        db_obj = EmployeeAccountDetailsDb(
            **data,
            created_at=now,
            updated_at=now,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: EmployeeAccountDetailsDb,
        obj_in: Union[EmployeeAccountDetailsUpdate, Dict[str, Any]],
    ) -> EmployeeAccountDetailsDb:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def create_or_update(
        self,
        db: Session,
        *,
        employee_id: int,
        obj_in: Union[EmployeeAccountDetailsCreate, EmployeeAccountDetailsUpdate, Dict[str, Any]],
    ) -> EmployeeAccountDetailsDb:
        existing = self.get(db, employee_id=employee_id)
        if existing:
            return self.update(db, db_obj=existing, obj_in=obj_in)

        if isinstance(obj_in, dict):
            create_dict = {**obj_in, "employee_id": employee_id}
            create_schema = EmployeeAccountDetailsCreate(**create_dict)
        elif isinstance(obj_in, EmployeeAccountDetailsCreate):
            create_schema = obj_in
        else:
            create_dict = {**obj_in.model_dump(exclude_unset=True), "employee_id": employee_id}
            create_schema = EmployeeAccountDetailsCreate(**create_dict)

        return self.create(db, obj_in=create_schema)

    def remove(self, db: Session, *, employee_id: int) -> Optional[EmployeeAccountDetailsDb]:
        db_obj = self.get(db, employee_id=employee_id)
        if db_obj:
            db.delete(db_obj)
            db.commit()
        return db_obj


CRUD_EMPLOYEE_ACCOUNT_DETAILS = CRUDEmployeeAccountDetails()
