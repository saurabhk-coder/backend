from typing import Any, List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ....schemas.role import (
    RoleCreate,
    RoleDeleteResponse,
    RoleListResponse,
    RolePermissionsResponse,
    RolePermissionsUpdate,
    RoleResponse,
    RoleUpdate,
)
from ....services.role_service import ROLE_SERVICE
from ...deps import get_db

roles = APIRouter()


@roles.post(
    "",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create role",
)
@roles.post(
    "/",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_role(
    *,
    db: Session = Depends(get_db),
    role_in: RoleCreate,
) -> RoleResponse:
    """
    Create a new role with specified name, description, and permissions.
    """
    return ROLE_SERVICE.create_role(db, role_in)


@roles.get(
    "",
    response_model=List[RoleResponse],
    summary="List roles",
)
@roles.get(
    "/",
    response_model=List[RoleResponse],
    include_in_schema=False,
)
def list_roles(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records to return"),
    search: Optional[str] = Query(None, description="Filter roles by name or description"),
) -> List[RoleResponse]:
    """
    List all roles with optional pagination and search filter.
    """
    return ROLE_SERVICE.get_roles(db, skip=skip, limit=limit, search=search)


@roles.get(
    "/{role_id}",
    response_model=RoleResponse,
    summary="Get role",
)
def get_role(
    *,
    db: Session = Depends(get_db),
    role_id: str,
) -> RoleResponse:
    """
    Get details of a specific role by its ID.
    """
    return ROLE_SERVICE.get_role_by_id(db, role_id)


@roles.patch(
    "/{role_id}",
    response_model=RoleResponse,
    summary="Update role",
)
def update_role(
    *,
    db: Session = Depends(get_db),
    role_id: str,
    role_in: RoleUpdate,
) -> RoleResponse:
    """
    Update an existing role's name, description, or permissions.
    """
    return ROLE_SERVICE.update_role(db, role_id, role_in)


@roles.delete(
    "/{role_id}",
    response_model=RoleDeleteResponse,
    summary="Delete role",
)
def delete_role(
    *,
    db: Session = Depends(get_db),
    role_id: str,
) -> RoleDeleteResponse:
    """
    Delete a role by its ID.
    """
    return ROLE_SERVICE.delete_role(db, role_id)


@roles.get(
    "/{role_id}/permissions",
    response_model=RolePermissionsResponse,
    summary="Get permissions",
)
def get_permissions(
    *,
    db: Session = Depends(get_db),
    role_id: str,
) -> RolePermissionsResponse:
    """
    Get the permissions configured for a specific role.
    """
    return ROLE_SERVICE.get_permissions(db, role_id)


@roles.put(
    "/{role_id}/permissions",
    response_model=RolePermissionsResponse,
    summary="Replace permissions",
)
def replace_permissions(
    *,
    db: Session = Depends(get_db),
    role_id: str,
    payload: Any = Body(..., description="Replacement permissions payload (dict, list, or JSON object)"),
) -> RolePermissionsResponse:
    """
    Replace the permissions for a specific role.
    Accepts raw JSON (list or object) or structured payload with 'permissions'/'permissions_json' key.
    """
    return ROLE_SERVICE.replace_permissions(db, role_id, payload)
