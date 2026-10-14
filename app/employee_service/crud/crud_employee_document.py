import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..models.employee_document import EmployeeDocumentDb
from ..schemas.employee_document import EmployeeDocumentCreate, EmployeeDocumentUpdate


class CRUDEmployeeDocument:
    def get(self, db: Session, document_id: Union[uuid.UUID, str]) -> Optional[EmployeeDocumentDb]:
        try:
            doc_uuid = uuid.UUID(str(document_id)) if not isinstance(document_id, uuid.UUID) else document_id
            return (
                db.query(EmployeeDocumentDb)
                .filter(EmployeeDocumentDb.id == doc_uuid)
                .first()
            )
        except (ValueError, TypeError):
            return None

    def get_by_employee(
        self,
        db: Session,
        employee_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[EmployeeDocumentDb]:
        query = db.query(EmployeeDocumentDb).filter(EmployeeDocumentDb.employee_id == employee_id)
        if category:
            query = query.filter(EmployeeDocumentDb.file_category == category.lower().strip())
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    EmployeeDocumentDb.file_name.ilike(pattern),
                    EmployeeDocumentDb.file_title.ilike(pattern),
                    EmployeeDocumentDb.description.ilike(pattern),
                    EmployeeDocumentDb.file_category.ilike(pattern),
                )
            )
        return (
            query.order_by(EmployeeDocumentDb.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_by_employee(
        self,
        db: Session,
        employee_id: int,
        *,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> int:
        query = db.query(func.count(EmployeeDocumentDb.id)).filter(
            EmployeeDocumentDb.employee_id == employee_id
        )
        if category:
            query = query.filter(EmployeeDocumentDb.file_category == category.lower().strip())
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    EmployeeDocumentDb.file_name.ilike(pattern),
                    EmployeeDocumentDb.file_title.ilike(pattern),
                    EmployeeDocumentDb.description.ilike(pattern),
                    EmployeeDocumentDb.file_category.ilike(pattern),
                )
            )
        return query.scalar() or 0

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        employee_id: Optional[int] = None,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[EmployeeDocumentDb]:
        query = db.query(EmployeeDocumentDb)
        if employee_id is not None:
            query = query.filter(EmployeeDocumentDb.employee_id == employee_id)
        if organization_id is not None:
            try:
                org_uuid = (
                    uuid.UUID(str(organization_id))
                    if not isinstance(organization_id, uuid.UUID)
                    else organization_id
                )
                query = query.filter(EmployeeDocumentDb.organization_id == org_uuid)
            except (ValueError, TypeError):
                pass
        if category:
            query = query.filter(EmployeeDocumentDb.file_category == category.lower().strip())
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    EmployeeDocumentDb.file_name.ilike(pattern),
                    EmployeeDocumentDb.file_title.ilike(pattern),
                    EmployeeDocumentDb.description.ilike(pattern),
                    EmployeeDocumentDb.file_category.ilike(pattern),
                )
            )
        return (
            query.order_by(EmployeeDocumentDb.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count(
        self,
        db: Session,
        *,
        employee_id: Optional[int] = None,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> int:
        query = db.query(func.count(EmployeeDocumentDb.id))
        if employee_id is not None:
            query = query.filter(EmployeeDocumentDb.employee_id == employee_id)
        if organization_id is not None:
            try:
                org_uuid = (
                    uuid.UUID(str(organization_id))
                    if not isinstance(organization_id, uuid.UUID)
                    else organization_id
                )
                query = query.filter(EmployeeDocumentDb.organization_id == org_uuid)
            except (ValueError, TypeError):
                pass
        if category:
            query = query.filter(EmployeeDocumentDb.file_category == category.lower().strip())
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    EmployeeDocumentDb.file_name.ilike(pattern),
                    EmployeeDocumentDb.file_title.ilike(pattern),
                    EmployeeDocumentDb.description.ilike(pattern),
                    EmployeeDocumentDb.file_category.ilike(pattern),
                )
            )
        return query.scalar() or 0

    def create(
        self, db: Session, *, obj_in: EmployeeDocumentCreate
    ) -> EmployeeDocumentDb:
        now = datetime.now(timezone.utc)
        data = obj_in.model_dump()
        db_obj = EmployeeDocumentDb(
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
        db_obj: EmployeeDocumentDb,
        obj_in: Union[EmployeeDocumentUpdate, Dict[str, Any]],
    ) -> EmployeeDocumentDb:
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

    def remove(
        self, db: Session, *, document_id: Union[uuid.UUID, str]
    ) -> Optional[EmployeeDocumentDb]:
        db_obj = self.get(db, document_id=document_id)
        if db_obj:
            db.delete(db_obj)
            db.commit()
        return db_obj


CRUD_EMPLOYEE_DOCUMENT = CRUDEmployeeDocument()
