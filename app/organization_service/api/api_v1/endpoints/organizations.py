from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ....schemas.organization import (
    OrganizationCreate,
    OrganizationDeactivateResponse,
    OrganizationListResponse,
    OrganizationResponse,
    OrganizationSummaryResponse,
    OrganizationUpdate,
)
from ....services.organization_service import ORGANIZATION_SERVICE
from ...deps import get_db

organizations = APIRouter()


@organizations.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create organization",
)
@organizations.post(
    "/",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_organization(
    *,
    db: Session = Depends(get_db),
    org_in: OrganizationCreate,
) -> OrganizationResponse:
    """
    Create a new organization with specified details.
    """
    return ORGANIZATION_SERVICE.create_organization(db, org_in)


@organizations.get(
    "",
    response_model=List[OrganizationResponse],
    summary="List organizations (platform admin)",
)
@organizations.get(
    "/",
    response_model=List[OrganizationResponse],
    include_in_schema=False,
)
def list_organizations(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records to return"),
    search: Optional[str] = Query(None, description="Filter by name, slug, email, city, or country"),
    status: Optional[str] = Query(None, description="Filter by status (e.g. active, inactive)"),
) -> List[OrganizationResponse]:
    """
    List all organizations with optional pagination, search, and status filter.
    """
    return ORGANIZATION_SERVICE.get_organizations(
        db, skip=skip, limit=limit, search=search, status=status
    )


@organizations.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Get organization",
)
def get_organization(
    *,
    db: Session = Depends(get_db),
    organization_id: str,
) -> OrganizationResponse:
    """
    Get details of a specific organization by its ID.
    """
    return ORGANIZATION_SERVICE.get_organization_by_id(db, organization_id)


@organizations.patch(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Update organization",
)
def update_organization(
    *,
    db: Session = Depends(get_db),
    organization_id: str,
    org_in: OrganizationUpdate,
) -> OrganizationResponse:
    """
    Update details of an existing organization.
    """
    return ORGANIZATION_SERVICE.update_organization(db, organization_id, org_in)


@organizations.delete(
    "/{organization_id}",
    response_model=OrganizationDeactivateResponse,
    summary="Deactivate organization",
)
def deactivate_organization(
    *,
    db: Session = Depends(get_db),
    organization_id: str,
) -> OrganizationDeactivateResponse:
    """
    Deactivate an organization (sets status to 'inactive').
    """
    return ORGANIZATION_SERVICE.deactivate_organization(db, organization_id)


@organizations.get(
    "/{organization_id}/summary",
    response_model=OrganizationSummaryResponse,
    summary="Organization summary",
)
def get_organization_summary(
    *,
    db: Session = Depends(get_db),
    organization_id: str,
) -> OrganizationSummaryResponse:
    """
    Get summary metrics for an organization including member counts.
    """
    return ORGANIZATION_SERVICE.get_summary(db, organization_id)
