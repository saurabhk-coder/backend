import uuid
from typing import Generator, Optional
from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core import AppSettings
from app.auth_service.db.session import SessionLocal
from app.user_service.models.user import UsersDb
from app.employee_service.models import EmployeeDb, EmployeePersonalInformationDb
from app.organization_service.models.organization import OrganizationDb
from app.role_service.models.role import RoleDb

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{AppSettings.API.API_V1_STR}/auth/login",
    auto_error=False,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CurrentAuth:
    def __init__(
        self,
        user: Optional[UsersDb],
        role_name: str,
        employee_id: Optional[int],
        organization_id: uuid.UUID,
    ):
        self.user = user
        self.role_name = (role_name or "Employee").strip()
        self.employee_id = employee_id
        self.organization_id = organization_id

    @property
    def is_admin(self) -> bool:
        r = self.role_name.upper()
        return "ADMIN" in r or "SUPER" in r

    @property
    def is_manager_or_lead(self) -> bool:
        r = self.role_name.upper()
        return self.is_admin or "MANAGER" in r or "LEAD" in r or "EXECUTIVE" in r


def get_current_auth(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(reusable_oauth2),
    authorization: Optional[str] = Header(None),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
) -> CurrentAuth:
    raw_token = token
    if not raw_token and authorization:
        if authorization.startswith("Bearer "):
            raw_token = authorization[7:].strip()
        else:
            raw_token = authorization.strip()

    if raw_token:
        try:
            payload = jwt.decode(
                raw_token,
                AppSettings.API.SECRET_KEY,
                algorithms=[AppSettings.API.ALGORITHM],
            )
            user_id_str = payload.get("sub")
            if not user_id_str:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                )
            user_id = uuid.UUID(str(user_id_str))
        except (JWTError, ValidationError, ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = db.query(UsersDb).filter(UsersDb.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticated user no longer exists",
            )

        org_id = user.organization_id
        if not org_id:
            first_org = db.query(OrganizationDb).first()
            org_id = first_org.id if first_org else uuid.uuid4()

        if x_organization_id:
            try:
                req_org_id = uuid.UUID(str(x_organization_id).strip())
                if req_org_id != org_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Organization not found",
                    )
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invalid organization ID",
                )

        role_name = "Employee"
        if user.role_id:
            role_db = db.query(RoleDb).filter(RoleDb.id == user.role_id).first()
            if role_db and role_db.name:
                role_name = role_db.name

        emp_id = None
        if user.email:
            emp_personal = (
                db.query(EmployeePersonalInformationDb)
                .filter(
                    EmployeePersonalInformationDb.organization_id == org_id,
                    EmployeePersonalInformationDb.email.ilike(user.email.strip()),
                )
                .first()
            )
            if emp_personal:
                emp_id = emp_personal.employee_id

        if not emp_id:
            first_emp = (
                db.query(EmployeePersonalInformationDb)
                .filter(EmployeePersonalInformationDb.organization_id == org_id)
                .first()
            )
            if first_emp:
                emp_id = first_emp.employee_id
            else:
                emp_id = 1

        return CurrentAuth(
            user=user,
            role_name=role_name,
            employee_id=emp_id,
            organization_id=org_id,
        )

    # Fallback when no token is provided (dev/testing mode or explicit org/emp)
    org_id = None
    if x_organization_id:
        try:
            org_id = uuid.UUID(str(x_organization_id).strip())
        except (ValueError, TypeError):
            pass

    if not org_id:
        first_org = db.query(OrganizationDb).first()
        org_id = first_org.id if first_org else uuid.uuid4()

    first_emp = (
        db.query(EmployeePersonalInformationDb)
        .filter(EmployeePersonalInformationDb.organization_id == org_id)
        .first()
    )
    if first_emp:
        emp_id = first_emp.employee_id
    else:
        first_emp_rec = db.query(EmployeeDb).first()
        emp_id = first_emp_rec.id if first_emp_rec else 1

    first_user = db.query(UsersDb).filter(UsersDb.organization_id == org_id).first()

    return CurrentAuth(
        user=first_user,
        role_name="Super Admin",
        employee_id=emp_id,
        organization_id=org_id,
    )


def get_strict_auth(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(reusable_oauth2),
    authorization: Optional[str] = Header(None),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
) -> CurrentAuth:
    raw_token = token
    if not raw_token and authorization:
        if authorization.startswith("Bearer "):
            raw_token = authorization[7:].strip()
        else:
            raw_token = authorization.strip()

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return get_current_auth(
        db=db,
        token=raw_token,
        authorization=authorization,
        x_organization_id=x_organization_id,
    )
