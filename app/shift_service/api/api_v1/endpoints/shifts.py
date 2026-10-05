import uuid
from typing import Optional
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, status
from jose import jwt
from sqlalchemy.orm import Session

from app.core import AppSettings
from app.organization_service.models.organization import OrganizationDb
from ....schemas.shift import (
    ShiftCreate,
    ShiftDeleteResponse,
    ShiftListResponse,
    ShiftResponse,
    ShiftUpdate,
)
from ....services.shift_service import SHIFT_SERVICE
from ...deps import get_db

shifts = APIRouter()


def _resolve_organization_id(
    db: Session,
    organization_id: Optional[str] = None,
    x_organization_id: Optional[str] = None,
    authorization: Optional[str] = None,
) -> Optional[uuid.UUID]:
    """
    Resolve organization ID from:
    1. Explicit organization_id param
    2. X-Organization-Id header
    3. JWT Bearer token
    4. Fallback to single organization if only one exists in DB
    """
    if organization_id:
        try:
            return uuid.UUID(str(organization_id).strip())
        except (ValueError, TypeError):
            pass

    if x_organization_id:
        try:
            return uuid.UUID(str(x_organization_id).strip())
        except (ValueError, TypeError):
            pass

    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        try:
            payload = jwt.decode(
                token,
                AppSettings.API.SECRET_KEY,
                algorithms=[AppSettings.API.ALGORITHM],
            )
            user_id = payload.get("sub")
            if user_id:
                from app.user_service.models.user import UsersDb
                user = (
                    db.query(UsersDb)
                    .filter(UsersDb.id == uuid.UUID(str(user_id)))
                    .first()
                )
                if user and user.organization_id:
                    return user.organization_id
        except Exception:
            pass

    first_org = db.query(OrganizationDb).first()
    if first_org:
        total_orgs = db.query(OrganizationDb).count()
        if total_orgs == 1:
            return first_org.id

    return None


@shifts.get(
    "",
    response_model=ShiftListResponse,
    summary="List all shifts",
)
@shifts.get(
    "/",
    response_model=ShiftListResponse,
    include_in_schema=False,
)
def list_shifts(
    *,
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search by shift name, department, or location"),
    department: Optional[str] = Query(None, description="Filter by department"),
    location: Optional[str] = Query(None, description="Filter by office location"),
    is_active: Optional[bool] = Query(None, description="Filter active/inactive"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=1000, description="Items per page"),
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
    authorization: Optional[str] = Header(None),
) -> ShiftListResponse:
    """
    List all shifts with pagination and filters.
    """
    org_id = _resolve_organization_id(
        db,
        organization_id=organization_id,
        x_organization_id=x_organization_id,
        authorization=authorization,
    )
    return SHIFT_SERVICE.list_shifts(
        db,
        organization_id=org_id,
        search=search,
        department=department,
        location=location,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )


@shifts.get(
    "/{id}",
    response_model=ShiftResponse,
    summary="Get single shift by ID",
)
def get_shift(
    *,
    db: Session = Depends(get_db),
    id: str,
    organization_id: Optional[str] = Query(None, description="Organization ID"),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
    authorization: Optional[str] = Header(None),
) -> ShiftResponse:
    """
    Get details of a specific shift by its ID.
    """
    org_id = _resolve_organization_id(
        db,
        organization_id=organization_id,
        x_organization_id=x_organization_id,
        authorization=authorization,
    )
    return SHIFT_SERVICE.get_shift(
        db,
        id=id,
        organization_id=org_id,
    )


@shifts.post(
    "",
    response_model=ShiftResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create shift",
)
@shifts.post(
    "/",
    response_model=ShiftResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_shift(
    *,
    db: Session = Depends(get_db),
    payload: ShiftCreate = Body(...),
    organization_id: Optional[str] = Query(None, description="Organization ID"),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
    authorization: Optional[str] = Header(None),
) -> ShiftResponse:
    """
    Create a new shift policy configuration.
    """
    target_org_id = payload.organizationId or _resolve_organization_id(
        db,
        organization_id=organization_id,
        x_organization_id=x_organization_id,
        authorization=authorization,
    )

    if not target_org_id:
        fallback_org = db.query(OrganizationDb).first()
        if fallback_org:
            target_org_id = fallback_org.id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization ID is required to create a shift",
            )

    return SHIFT_SERVICE.create_shift(
        db,
        organization_id=target_org_id,
        obj_in=payload,
    )


@shifts.put(
    "/{id}",
    response_model=ShiftResponse,
    summary="Update shift",
)
def update_shift(
    *,
    db: Session = Depends(get_db),
    id: str,
    payload: ShiftUpdate = Body(...),
    organization_id: Optional[str] = Query(None, description="Organization ID"),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
    authorization: Optional[str] = Header(None),
) -> ShiftResponse:
    """
    Update an existing shift policy by ID.
    """
    org_id = payload.organizationId or _resolve_organization_id(
        db,
        organization_id=organization_id,
        x_organization_id=x_organization_id,
        authorization=authorization,
    )
    return SHIFT_SERVICE.update_shift(
        db,
        id=id,
        obj_in=payload,
        organization_id=org_id,
    )


@shifts.delete(
    "/{id}",
    response_model=ShiftDeleteResponse,
    summary="Delete shift",
)
def delete_shift(
    *,
    db: Session = Depends(get_db),
    id: str,
    organization_id: Optional[str] = Query(None, description="Organization ID"),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
    authorization: Optional[str] = Header(None),
) -> ShiftDeleteResponse:
    """
    Delete a shift policy by ID.
    """
    org_id = _resolve_organization_id(
        db,
        organization_id=organization_id,
        x_organization_id=x_organization_id,
        authorization=authorization,
    )
    return SHIFT_SERVICE.delete_shift(
        db,
        id=id,
        organization_id=org_id,
    )
