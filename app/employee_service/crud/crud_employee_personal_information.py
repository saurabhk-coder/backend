import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from passlib.context import CryptContext
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..models.employee_personal_information import EmployeePersonalInformationDb
from ..schemas.employee_personal_information import (
    EmployeePersonalInformationCreate,
    EmployeePersonalInformationUpdate,
)
from app.user_service.models.user import UsersDb

logger = logging.getLogger(__name__)
PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _to_uuid(val: Union[uuid.UUID, str, None]) -> Optional[uuid.UUID]:
    if val is None:
        return None
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val).strip())
    except (ValueError, TypeError, AttributeError):
        return None


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
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> List[EmployeePersonalInformationDb]:
        query = db.query(EmployeePersonalInformationDb)
        if organization_id:
            org_uuid = _to_uuid(organization_id)
            if org_uuid:
                query = query.filter(EmployeePersonalInformationDb.organization_id == org_uuid)
            else:
                return []
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

    def count(
        self,
        db: Session,
        *,
        search: Optional[str] = None,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> int:
        query = db.query(func.count(EmployeePersonalInformationDb.employee_id))
        if organization_id:
            org_uuid = _to_uuid(organization_id)
            if org_uuid:
                query = query.filter(EmployeePersonalInformationDb.organization_id == org_uuid)
            else:
                return 0
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

    def _sync_user(
        self,
        db: Session,
        *,
        employee_id: int,
        email: Optional[str],
        first_name: Optional[str],
        last_name: Optional[str],
        organization_id: Optional[Union[uuid.UUID, str]],
        now: datetime,
    ) -> Optional[UsersDb]:
        user_email = (
            email.strip().lower()
            if (email and email.strip())
            else f"emp_{employee_id}@placeholder.local"
        )
        existing_user = (
            db.query(UsersDb)
            .filter(func.lower(UsersDb.email) == func.lower(user_email))
            .first()
        )
        org_uuid = _to_uuid(organization_id) if organization_id else None
        if org_uuid:
            try:
                from app.organization_service.models.organization import OrganizationDb
                org_exists = db.query(OrganizationDb.id).filter(OrganizationDb.id == org_uuid).first()
                if not org_exists:
                    org_uuid = None
            except Exception:
                pass
        hashed_password = PWD_CONTEXT.hash("admin")

        if not existing_user:
            new_user = UsersDb(
                id=uuid.uuid4(),
                organization_id=org_uuid,
                email=user_email,
                password_salt=hashed_password,
                first_name=first_name,
                last_name=last_name,
                country_code="US",
                status="inactive",
                is_active=False,
                created_at=now,
                updated_at=now,
            )
            db.add(new_user)
            return new_user
        else:
            if org_uuid:
                existing_user.organization_id = org_uuid
            if first_name:
                existing_user.first_name = first_name
            if last_name:
                existing_user.last_name = last_name
            existing_user.status = "inactive"
            existing_user.is_active = False
            if not existing_user.password_salt:
                existing_user.password_salt = hashed_password
            existing_user.updated_at = now
            db.add(existing_user)
            return existing_user

    def create(
        self, db: Session, *, obj_in: EmployeePersonalInformationCreate
    ) -> EmployeePersonalInformationDb:
        now = datetime.now(timezone.utc)
        data = obj_in.model_dump()
        if "organization_id" in data and data["organization_id"] is not None:
            data["organization_id"] = _to_uuid(data["organization_id"])

        db_obj = EmployeePersonalInformationDb(
            **data,
            created_at=now,
            updated_at=now,
        )
        db.add(db_obj)

        # Automatically insert or sync into UsersDb (hrms.users)
        # Status is inactive and password is admin
        try:
            with db.begin_nested():
                self._sync_user(
                    db,
                    employee_id=obj_in.employee_id,
                    email=obj_in.email,
                    first_name=obj_in.first_name,
                    last_name=obj_in.last_name,
                    organization_id=obj_in.organization_id,
                    now=now,
                )
        except Exception as exc:
            logger.exception("Failed to sync user in users table during employee creation: %s", exc)

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
            if field == "organization_id" and value is not None:
                value = _to_uuid(value)
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)

        # Automatically insert or sync into UsersDb (hrms.users)
        # Status is inactive and password is admin
        try:
            with db.begin_nested():
                self._sync_user(
                    db,
                    employee_id=db_obj.employee_id,
                    email=db_obj.email,
                    first_name=db_obj.first_name,
                    last_name=db_obj.last_name,
                    organization_id=db_obj.organization_id,
                    now=db_obj.updated_at,
                )
        except Exception as exc:
            logger.exception("Failed to sync user in users table during employee update: %s", exc)

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
