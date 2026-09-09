from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..models.employee_personal_information import EmployeePersonalInformationDb
from ..schemas.employee_personal_information import (
    EmployeePersonalInformationCreate,
    EmployeePersonalInformationUpdate,
)


class CRUDEmployeePersonalInformation:
    def get(self, db: Session, employee_id: int) -> Optional[EmployeePersonalInformationDb]:
        try:
            return (
                db.query(EmployeePersonalInformationDb)
                .filter(EmployeePersonalInformationDb.employee_id == employee_id)
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
    ) -> List[EmployeePersonalInformationDb]:
        query = db.query(EmployeePersonalInformationDb)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    EmployeePersonalInformationDb.first_name.ilike(pattern),
                    EmployeePersonalInformationDb.last_name.ilike(pattern),
                    EmployeePersonalInformationDb.email.ilike(pattern),
                    EmployeePersonalInformationDb.mobile_number.ilike(pattern),
                    EmployeePersonalInformationDb.city.ilike(pattern),
                    EmployeePersonalInformationDb.state.ilike(pattern),
                    EmployeePersonalInformationDb.nationality.ilike(pattern),
                )
            )
        return (
            query.order_by(EmployeePersonalInformationDb.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count(self, db: Session, *, search: Optional[str] = None) -> int:
        query = db.query(func.count(EmployeePersonalInformationDb.employee_id))
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    EmployeePersonalInformationDb.first_name.ilike(pattern),
                    EmployeePersonalInformationDb.last_name.ilike(pattern),
                    EmployeePersonalInformationDb.email.ilike(pattern),
                    EmployeePersonalInformationDb.mobile_number.ilike(pattern),
                    EmployeePersonalInformationDb.city.ilike(pattern),
                    EmployeePersonalInformationDb.state.ilike(pattern),
                    EmployeePersonalInformationDb.nationality.ilike(pattern),
                )
            )
        return query.scalar() or 0

    def create(
        self, db: Session, *, obj_in: EmployeePersonalInformationCreate
    ) -> EmployeePersonalInformationDb:
        now = datetime.now(timezone.utc)
        data = obj_in.model_dump()
        db_obj = EmployeePersonalInformationDb(
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
        db_obj: EmployeePersonalInformationDb,
        obj_in: Union[EmployeePersonalInformationUpdate, Dict[str, Any]],
    ) -> EmployeePersonalInformationDb:
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
        obj_in: Union[EmployeePersonalInformationCreate, EmployeePersonalInformationUpdate, Dict[str, Any]],
    ) -> EmployeePersonalInformationDb:
        existing = self.get(db, employee_id=employee_id)
        if existing:
            return self.update(db, db_obj=existing, obj_in=obj_in)

        if isinstance(obj_in, dict):
            create_dict = {**obj_in, "employee_id": employee_id}
            create_schema = EmployeePersonalInformationCreate(**create_dict)
        elif isinstance(obj_in, EmployeePersonalInformationCreate):
            create_schema = obj_in
        else:
            create_dict = {**obj_in.model_dump(exclude_unset=True), "employee_id": employee_id}
            create_schema = EmployeePersonalInformationCreate(**create_dict)

        return self.create(db, obj_in=create_schema)

    def remove(self, db: Session, *, employee_id: int) -> Optional[EmployeePersonalInformationDb]:
        db_obj = self.get(db, employee_id=employee_id)
        if db_obj:
            db.delete(db_obj)
            db.commit()
        return db_obj


CRUD_EMPLOYEE_PERSONAL_INFORMATION = CRUDEmployeePersonalInformation()
