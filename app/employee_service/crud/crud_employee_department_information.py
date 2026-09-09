from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..models.employee_department_information import EmployeeDepartmentInformationDb
from ..schemas.employee_department_information import (
    EmployeeDepartmentInformationCreate,
    EmployeeDepartmentInformationUpdate,
)


class CRUDEmployeeDepartmentInformation:
    def get(self, db: Session, employee_id: int) -> Optional[EmployeeDepartmentInformationDb]:
        try:
            return (
                db.query(EmployeeDepartmentInformationDb)
                .filter(EmployeeDepartmentInformationDb.employee_id == employee_id)
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
    ) -> List[EmployeeDepartmentInformationDb]:
        query = db.query(EmployeeDepartmentInformationDb)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    EmployeeDepartmentInformationDb.department.ilike(pattern),
                    EmployeeDepartmentInformationDb.designation.ilike(pattern),
                    EmployeeDepartmentInformationDb.work_location.ilike(pattern),
                    EmployeeDepartmentInformationDb.work_mode.ilike(pattern),
                    EmployeeDepartmentInformationDb.employment_type.ilike(pattern),
                )
            )
        return (
            query.order_by(EmployeeDepartmentInformationDb.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count(self, db: Session, *, search: Optional[str] = None) -> int:
        query = db.query(func.count(EmployeeDepartmentInformationDb.employee_id))
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    EmployeeDepartmentInformationDb.department.ilike(pattern),
                    EmployeeDepartmentInformationDb.designation.ilike(pattern),
                    EmployeeDepartmentInformationDb.work_location.ilike(pattern),
                    EmployeeDepartmentInformationDb.work_mode.ilike(pattern),
                    EmployeeDepartmentInformationDb.employment_type.ilike(pattern),
                )
            )
        return query.scalar() or 0

    def create(
        self, db: Session, *, obj_in: EmployeeDepartmentInformationCreate
    ) -> EmployeeDepartmentInformationDb:
        now = datetime.now(timezone.utc)
        data = obj_in.model_dump()
        db_obj = EmployeeDepartmentInformationDb(
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
        db_obj: EmployeeDepartmentInformationDb,
        obj_in: Union[EmployeeDepartmentInformationUpdate, Dict[str, Any]],
    ) -> EmployeeDepartmentInformationDb:
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
        obj_in: Union[EmployeeDepartmentInformationCreate, EmployeeDepartmentInformationUpdate, Dict[str, Any]],
    ) -> EmployeeDepartmentInformationDb:
        existing = self.get(db, employee_id=employee_id)
        if existing:
            return self.update(db, db_obj=existing, obj_in=obj_in)

        if isinstance(obj_in, dict):
            create_dict = {**obj_in, "employee_id": employee_id}
            create_schema = EmployeeDepartmentInformationCreate(**create_dict)
        elif isinstance(obj_in, EmployeeDepartmentInformationCreate):
            create_schema = obj_in
        else:
            create_dict = {**obj_in.model_dump(exclude_unset=True), "employee_id": employee_id}
            create_schema = EmployeeDepartmentInformationCreate(**create_dict)

        return self.create(db, obj_in=create_schema)

    def remove(self, db: Session, *, employee_id: int) -> Optional[EmployeeDepartmentInformationDb]:
        db_obj = self.get(db, employee_id=employee_id)
        if db_obj:
            db.delete(db_obj)
            db.commit()
        return db_obj


CRUD_EMPLOYEE_DEPARTMENT_INFORMATION = CRUDEmployeeDepartmentInformation()
