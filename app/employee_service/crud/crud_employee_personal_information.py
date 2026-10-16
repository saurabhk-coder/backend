import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..models.employee import EmployeeDb
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

    def get_by_email(self, db: Session, email: str) -> Optional[EmployeePersonalInformationDb]:
        if not email or not str(email).strip():
            return None
        return (
            db.query(EmployeePersonalInformationDb)
            .filter(func.lower(EmployeePersonalInformationDb.email) == str(email).strip().lower())
            .first()
        )

    def get_by_mobile_number(
        self, db: Session, mobile_number: str
    ) -> Optional[EmployeePersonalInformationDb]:
        if not mobile_number or not str(mobile_number).strip():
            return None
        return (
            db.query(EmployeePersonalInformationDb)
            .filter(EmployeePersonalInformationDb.mobile_number == str(mobile_number).strip())
            .first()
        )

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
        password: Optional[str] = "admin",
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
                if db.bind and db.bind.dialect.name != "sqlite":
                    org_exists = db.query(OrganizationDb.id).filter(OrganizationDb.id == org_uuid).first()
                    if not org_exists:
                        org_uuid = None
            except Exception:
                pass

        user_password = password if (password and str(password).strip()) else "admin"
        hashed_password = PWD_CONTEXT.hash(user_password)

        if not existing_user:
            new_user = UsersDb(
                id=uuid.uuid4(),
                organization_id=org_uuid,
                email=user_email,
                password_salt=hashed_password,
                first_name=first_name,
                last_name=last_name,
                country_code="US",
                status="Aaralia",
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
            if not existing_user.status:
                existing_user.status = "active"
            if password and str(password).strip():
                existing_user.password_salt = hashed_password
            elif not existing_user.password_salt:
                existing_user.password_salt = hashed_password
            existing_user.updated_at = now
            db.add(existing_user)
            return existing_user

    def create(
        self, db: Session, *, obj_in: Union[EmployeePersonalInformationCreate, Dict[str, Any]]
    ) -> EmployeePersonalInformationDb:
        if isinstance(obj_in, dict):
            data = dict(obj_in)
            email_val = data.get("email")
            emp_id_val = data.get("employee_id")
            password_val = data.pop("password", None) or "admin"
        else:
            data = obj_in.model_dump()
            email_val = obj_in.email
            emp_id_val = obj_in.employee_id
            password_val = data.pop("password", None) or "admin"

        # 1. Check if employee already exists in employee personal information table by email
        existing = None
        if email_val and str(email_val).strip():
            existing = self.get_by_email(db, str(email_val).strip())

        # 2. Also check by employee_id if provided and not found by email
        if not existing and emp_id_val:
            existing = self.get(db, employee_id=emp_id_val)

        # 3. Check mobile number uniqueness
        mobile_val = data.get("mobile_number")
        if mobile_val and str(mobile_val).strip():
            clean_mobile = str(mobile_val).strip()
            existing_mobile = self.get_by_mobile_number(db, clean_mobile)
            if existing_mobile:
                if not existing or existing_mobile.employee_id != existing.employee_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Employee personal information with mobile number '{clean_mobile}' already exists",
                    )

        if existing:
            # Found in employee table: take employee_id from employee table and update information by email
            return self.update(db, db_obj=existing, obj_in=obj_in)

        # 4. Not found in employee table: create in EmployeeDb (employees table) and return
        if emp_id_val:
            emp = db.query(EmployeeDb).filter(EmployeeDb.id == emp_id_val).first()
            if not emp:
                emp = EmployeeDb(id=emp_id_val, employee_code=f"EMP-{emp_id_val:04d}")
                db.add(emp)
                db.flush()
            assigned_id = emp.id
        else:
            emp = EmployeeDb()
            if db.bind and db.bind.dialect.name == "sqlite":
                max_id = db.query(func.max(EmployeeDb.id)).scalar() or 0
                next_id = int(max_id) + 1
                emp.id = next_id
                emp.employee_code = f"EMP-{next_id:04d}"
            db.add(emp)
            db.flush()
            if not emp.employee_code:
                emp.employee_code = f"EMP-{emp.id:04d}"
                db.add(emp)
                db.flush()
            assigned_id = emp.id

        data["employee_id"] = assigned_id
        if "organization_id" in data and data["organization_id"] is not None:
            data["organization_id"] = _to_uuid(data["organization_id"])

        now = datetime.now(timezone.utc)
        db_obj = EmployeePersonalInformationDb(
            **data,
            created_at=now,
            updated_at=now,
        )
        db.add(db_obj)

        # Automatically insert or sync into UsersDb (hrms.users)
        # Status is active and default password is admin
        try:
            with db.begin_nested():
                self._sync_user(
                    db,
                    employee_id=assigned_id,
                    email=data.get("email"),
                    first_name=data.get("first_name"),
                    last_name=data.get("last_name"),
                    organization_id=data.get("organization_id"),
                    password=password_val,
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
            update_data = dict(obj_in)
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        password_val = update_data.pop("password", None)

        # Check mobile number uniqueness if mobile_number is being updated
        if "mobile_number" in update_data:
            mobile_val = update_data.get("mobile_number")
            if mobile_val and str(mobile_val).strip():
                clean_mobile = str(mobile_val).strip()
                existing_mobile = self.get_by_mobile_number(db, clean_mobile)
                if existing_mobile and existing_mobile.employee_id != db_obj.employee_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Employee personal information with mobile number '{clean_mobile}' already exists",
                    )

        for field, value in update_data.items():
            if field == "organization_id" and value is not None:
                value = _to_uuid(value)
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)

        # Automatically insert or sync into UsersDb (hrms.users)
        try:
            with db.begin_nested():
                self._sync_user(
                    db,
                    employee_id=db_obj.employee_id,
                    email=db_obj.email,
                    first_name=db_obj.first_name,
                    last_name=db_obj.last_name,
                    organization_id=db_obj.organization_id,
                    password=password_val,
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

    def update_by_email(
        self,
        db: Session,
        *,
        email: str,
        obj_in: Union[EmployeePersonalInformationUpdate, Dict[str, Any]],
    ) -> Optional[EmployeePersonalInformationDb]:
        record = self.get_by_email(db, email=email)
        if not record:
            return None
        return self.update(db, db_obj=record, obj_in=obj_in)

    def remove(self, db: Session, *, employee_id: int) -> Optional[EmployeePersonalInformationDb]:
        db_obj = self.get(db, employee_id=employee_id)
        if db_obj:
            db.delete(db_obj)
            db.commit()
        return db_obj


CRUD_EMPLOYEE_PERSONAL_INFORMATION = CRUDEmployeePersonalInformation()
