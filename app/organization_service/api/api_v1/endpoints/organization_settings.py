import json
from typing import Any, List, Optional
from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.orm import Session

from ....schemas.organization_setting import (
    OrganizationSettingCreateOrUpdate,
    OrganizationSettingDeleteResponse,
    OrganizationSettingListResponse,
    OrganizationSettingResponse,
)
from ....services.organization_setting_service import ORGANIZATION_SETTING_SERVICE
from ...deps import get_db

organization_settings = APIRouter()


@organization_settings.get(
    "/organizations/{organization_id}/settings",
    response_model=List[OrganizationSettingResponse],
    summary="List settings",
)
def list_settings(
    *,
    db: Session = Depends(get_db),
    organization_id: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records to return"),
) -> List[OrganizationSettingResponse]:
    """
    List all settings for a specific organization.
    """
    return ORGANIZATION_SETTING_SERVICE.get_settings(
        db, organization_id=organization_id, skip=skip, limit=limit
    )


@organization_settings.get(
    "/organizations/{organization_id}/settings/{setting_key}",
    response_model=OrganizationSettingResponse,
    summary="Get setting",
)
def get_setting(
    *,
    db: Session = Depends(get_db),
    organization_id: str,
    setting_key: str,
) -> OrganizationSettingResponse:
    """
    Get a specific setting by key for an organization.
    """
    return ORGANIZATION_SETTING_SERVICE.get_setting(
        db, organization_id=organization_id, setting_key=setting_key
    )


@organization_settings.put(
    "/organizations/{organization_id}/settings/{setting_key}",
    response_model=OrganizationSettingResponse,
    summary="Create or update setting",
)
def set_setting(
    *,
    db: Session = Depends(get_db),
    organization_id: str,
    setting_key: str,
    payload: Any = Body(
        None,
        description="Setting value payload (e.g. {'setting_value': '...'}, string, or JSON structure)",
    ),
) -> OrganizationSettingResponse:
    """
    Create or update a configuration setting for an organization.
    """
    if isinstance(payload, OrganizationSettingCreateOrUpdate):
        setting_val = payload.setting_value
    elif isinstance(payload, dict) and "setting_value" in payload and len(payload) <= 2:
        setting_val = (
            str(payload["setting_value"]) if payload["setting_value"] is not None else None
        )
    elif isinstance(payload, (dict, list)):
        setting_val = json.dumps(payload)
    elif payload is not None:
        setting_val = str(payload)
    else:
        setting_val = None

    return ORGANIZATION_SETTING_SERVICE.set_setting(
        db,
        organization_id=organization_id,
        setting_key=setting_key,
        setting_value=setting_val,
    )


@organization_settings.delete(
    "/organizations/{organization_id}/settings/{setting_key}",
    response_model=OrganizationSettingDeleteResponse,
    summary="Delete setting",
)
def delete_setting(
    *,
    db: Session = Depends(get_db),
    organization_id: str,
    setting_key: str,
) -> OrganizationSettingDeleteResponse:
    """
    Delete a specific setting by key for an organization.
    """
    return ORGANIZATION_SETTING_SERVICE.delete_setting(
        db, organization_id=organization_id, setting_key=setting_key
    )
