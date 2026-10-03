import uuid
from typing import Any, Optional
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Response, status
from jose import jwt
from sqlalchemy.orm import Session

from app.core import AppSettings
from ....crud.crud_organization import CRUD_ORGANIZATION
from ....models.organization import OrganizationDb
from ....schemas.calendar_setting import (
    CalendarSettingCreate,
    CalendarSettingDeleteResponse,
    CalendarSettingListResponse,
    CalendarSettingSingleResponse,
    CalendarSettingUpdate,
)
from ....services.calendar_setting_service import CALENDAR_SETTING_SERVICE
from ...deps import get_db


calendar_settings_router = APIRouter()


def _resolve_organization_id(
    db: Session,
    organization_id: Optional[str] = None,
    x_organization_id: Optional[str] = None,
    authorization: Optional[str] = None,
) -> Optional[uuid.UUID]:
    """
    Resolve the organization ID from:
    1. Explicit organization_id parameter
    2. X-Organization-Id request header
    3. JWT Bearer token sub -> user organization
    4. Fallback to the single existing organization if only one exists in DB
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

    # Fallback to single organization if only one exists in database
    first_org = db.query(OrganizationDb).first()
    if first_org:
        total_orgs = db.query(OrganizationDb).count()
        if total_orgs == 1:
            return first_org.id

    return None


@calendar_settings_router.get(
    "/settings/calendar",
    response_model=CalendarSettingListResponse,
    summary="List all calendar settings for current organization",
)
def list_calendar_settings(
    *,
    db: Session = Depends(get_db),
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    location: Optional[str] = Query(None, description="Filter by location name"),
    is_default: Optional[bool] = Query(None, description="Filter by default calendar flag"),
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
    authorization: Optional[str] = Header(None),
) -> CalendarSettingListResponse:
    """
    List all calendar settings for the current organization.
    """
    org_id = _resolve_organization_id(
        db,
        organization_id=organization_id,
        x_organization_id=x_organization_id,
        authorization=authorization,
    )
    return CALENDAR_SETTING_SERVICE.list_calendar_settings(
        db,
        organization_id=org_id,
        location=location,
        is_default=is_default,
        skip=skip,
        limit=limit,
    )


@calendar_settings_router.post(
    "/settings/calendar",
    response_model=CalendarSettingSingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or upsert calendar configuration",
)
def create_or_upsert_calendar_setting(
    *,
    db: Session = Depends(get_db),
    payload: CalendarSettingCreate = Body(...),
    organization_id: Optional[str] = Query(None, description="Organization ID"),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
    authorization: Optional[str] = Header(None),
    response: Response,
) -> CalendarSettingSingleResponse:
    """
    Create or upsert a calendar configuration for a location within an organization.
    """
    target_org_id = payload.organizationId or _resolve_organization_id(
        db,
        organization_id=organization_id,
        x_organization_id=x_organization_id,
        authorization=authorization,
    )

    if not target_org_id:
        # Check if an organization exists in DB to use
        fallback_org = db.query(OrganizationDb).first()
        if fallback_org:
            target_org_id = fallback_org.id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization ID is required to create a calendar setting",
            )

    result, is_new = CALENDAR_SETTING_SERVICE.create_or_upsert_calendar_setting(
        db,
        organization_id=target_org_id,
        obj_in=payload,
    )
    if not is_new:
        response.status_code = status.HTTP_200_OK
    return result


@calendar_settings_router.get(
    "/settings/calendar/{id}",
    response_model=CalendarSettingSingleResponse,
    summary="Fetch specific calendar setting by ID or location",
)
def get_calendar_setting(
    *,
    db: Session = Depends(get_db),
    id: str,
    organization_id: Optional[str] = Query(None, description="Organization ID"),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
    authorization: Optional[str] = Header(None),
) -> CalendarSettingSingleResponse:
    """
    Fetch a specific calendar setting by its ID or branch/office location.
    """
    org_id = _resolve_organization_id(
        db,
        organization_id=organization_id,
        x_organization_id=x_organization_id,
        authorization=authorization,
    )
    return CALENDAR_SETTING_SERVICE.get_calendar_setting(
        db,
        identifier=id,
        organization_id=org_id,
    )


@calendar_settings_router.put(
    "/settings/calendar/{id}",
    response_model=CalendarSettingSingleResponse,
    summary="Update an existing calendar setting",
)
def update_calendar_setting(
    *,
    db: Session = Depends(get_db),
    id: str,
    payload: CalendarSettingUpdate = Body(...),
    organization_id: Optional[str] = Query(None, description="Organization ID"),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
    authorization: Optional[str] = Header(None),
) -> CalendarSettingSingleResponse:
    """
    Update an existing calendar setting by its ID or location.
    """
    org_id = payload.organizationId or _resolve_organization_id(
        db,
        organization_id=organization_id,
        x_organization_id=x_organization_id,
        authorization=authorization,
    )
    return CALENDAR_SETTING_SERVICE.update_calendar_setting(
        db,
        identifier=id,
        obj_in=payload,
        organization_id=org_id,
    )


@calendar_settings_router.delete(
    "/settings/calendar/{id}",
    response_model=CalendarSettingDeleteResponse,
    summary="Remove calendar setting (fallback to organization default)",
)
def delete_calendar_setting(
    *,
    db: Session = Depends(get_db),
    id: str,
    organization_id: Optional[str] = Query(None, description="Organization ID"),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
    authorization: Optional[str] = Header(None),
) -> CalendarSettingDeleteResponse:
    """
    Remove calendar setting by ID or location.
    If the deleted setting was default, the oldest remaining calendar setting becomes the default fallback.
    """
    org_id = _resolve_organization_id(
        db,
        organization_id=organization_id,
        x_organization_id=x_organization_id,
        authorization=authorization,
    )
    return CALENDAR_SETTING_SERVICE.delete_calendar_setting(
        db,
        identifier=id,
        organization_id=org_id,
    )
