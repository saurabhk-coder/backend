from typing import Optional
from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.orm import Session

from ....schemas.employee_personal_information import (
    EmployeePersonalInformationBase,
    EmployeePersonalInformationCreate,
    EmployeePersonalInformationDeleteResponse,
    EmployeePersonalInformationListResponse,
    EmployeePersonalInformationResponse,
    EmployeePersonalInformationUpdate,
)
from ....services.employee_personal_information_service import (
    EMPLOYEE_PERSONAL_INFORMATION_SERVICE,
)
from ...deps import get_db

employee_personal_information_router = APIRouter()


@employee_personal_information_router.post(
    "/employee-personal-information",
    response_model=EmployeePersonalInformationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update employee personal information",
)
def create_personal_information(
    *,
    db: Session = Depends(get_db),
    payload: EmployeePersonalInformationCreate = Body(...),
) -> EmployeePersonalInformationResponse:
    """
    Create or update personal information for an employee.
    If the employee is not found in the employee table (by email), a new employee is created and returned.
    Otherwise, the employee is taken from the employee table and information is updated by email.
    """
    return EMPLOYEE_PERSONAL_INFORMATION_SERVICE.create(db, request=payload)


@employee_personal_information_router.get(
    "/employee-personal-information",
    response_model=EmployeePersonalInformationListResponse,
    summary="List employee personal information records",
)
def list_personal_information(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=1000, description="Max number of records to return"),
    search: Optional[str] = Query(None, description="Search query by name, email, phone, city, etc."),
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
) -> EmployeePersonalInformationListResponse:
    """
    Retrieve paginated employee personal information records with optional search filter.
    """
    return EMPLOYEE_PERSONAL_INFORMATION_SERVICE.get_multi(
        db, skip=skip, limit=limit, search=search, organization_id=organization_id
    )


@employee_personal_information_router.get(
    "/employee-personal-information/{employee_id}",
    response_model=EmployeePersonalInformationResponse,
    summary="Get employee personal information by employee ID",
)
def get_personal_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
) -> EmployeePersonalInformationResponse:
    """
    Retrieve personal information for a specific employee by employee_id.
    """
    return EMPLOYEE_PERSONAL_INFORMATION_SERVICE.get_by_employee_id(
        db, employee_id=employee_id
    )


@employee_personal_information_router.put(
    "/employee-personal-information/{employee_id}",
    response_model=EmployeePersonalInformationResponse,
    summary="Upsert or full update employee personal information",
)
def upsert_personal_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    payload: EmployeePersonalInformationUpdate = Body(...),
) -> EmployeePersonalInformationResponse:
    """
    Create or update personal information for a given employee_id (upsert).
    """
    return EMPLOYEE_PERSONAL_INFORMATION_SERVICE.upsert(
        db, employee_id=employee_id, request=payload
    )


@employee_personal_information_router.patch(
    "/employee-personal-information/{employee_id}",
    response_model=EmployeePersonalInformationResponse,
    summary="Partial update employee personal information",
)
def patch_personal_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    payload: EmployeePersonalInformationUpdate = Body(...),
) -> EmployeePersonalInformationResponse:
    """
    Partially update personal information fields for a specific employee.
    """
    return EMPLOYEE_PERSONAL_INFORMATION_SERVICE.update(
        db, employee_id=employee_id, request=payload
    )


@employee_personal_information_router.delete(
    "/employee-personal-information/{employee_id}",
    response_model=EmployeePersonalInformationDeleteResponse,
    summary="Delete employee personal information",
)
def delete_personal_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
) -> EmployeePersonalInformationDeleteResponse:
    """
    Delete personal information for a specific employee.
    """
    return EMPLOYEE_PERSONAL_INFORMATION_SERVICE.delete(db, employee_id=employee_id)


# ============================================================================
# Routes for email-based operations
# ============================================================================

@employee_personal_information_router.get(
    "/employee-personal-information/email/{email:path}",
    response_model=EmployeePersonalInformationResponse,
    summary="Get employee personal information by email",
)
def get_personal_information_by_email(
    *,
    db: Session = Depends(get_db),
    email: str,
) -> EmployeePersonalInformationResponse:
    """
    Retrieve personal information for a specific employee by email.
    """
    return EMPLOYEE_PERSONAL_INFORMATION_SERVICE.get_by_email(db, email=email)


@employee_personal_information_router.put(
    "/employee-personal-information/email/{email:path}",
    response_model=EmployeePersonalInformationResponse,
    summary="Update employee personal information by email",
)
def put_personal_information_by_email(
    *,
    db: Session = Depends(get_db),
    email: str,
    payload: EmployeePersonalInformationUpdate = Body(...),
) -> EmployeePersonalInformationResponse:
    """
    Update personal information for a specific employee by email.
    """
    return EMPLOYEE_PERSONAL_INFORMATION_SERVICE.update_by_email(
        db, email=email, request=payload
    )


@employee_personal_information_router.patch(
    "/employee-personal-information/email/{email:path}",
    response_model=EmployeePersonalInformationResponse,
    summary="Partial update employee personal information by email",
)
def patch_personal_information_by_email(
    *,
    db: Session = Depends(get_db),
    email: str,
    payload: EmployeePersonalInformationUpdate = Body(...),
) -> EmployeePersonalInformationResponse:
    """
    Partially update personal information fields for a specific employee by email.
    """
    return EMPLOYEE_PERSONAL_INFORMATION_SERVICE.update_by_email(
        db, email=email, request=payload
    )


# ============================================================================
# Nested routes for convenience: /employees/{employee_id}/personal-information
# ============================================================================

@employee_personal_information_router.get(
    "/employees/{employee_id}/personal-information",
    response_model=EmployeePersonalInformationResponse,
    summary="Get personal information (nested route)",
)
def get_nested_personal_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
) -> EmployeePersonalInformationResponse:
    return EMPLOYEE_PERSONAL_INFORMATION_SERVICE.get_by_employee_id(
        db, employee_id=employee_id
    )


@employee_personal_information_router.post(
    "/employees/{employee_id}/personal-information",
    response_model=EmployeePersonalInformationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create personal information (nested route)",
)
def create_nested_personal_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    payload: EmployeePersonalInformationCreate = Body(...),
) -> EmployeePersonalInformationResponse:
    payload.employee_id = employee_id
    return EMPLOYEE_PERSONAL_INFORMATION_SERVICE.create(db, request=payload)


@employee_personal_information_router.put(
    "/employees/{employee_id}/personal-information",
    response_model=EmployeePersonalInformationResponse,
    summary="Upsert personal information (nested route)",
)
def upsert_nested_personal_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    payload: EmployeePersonalInformationUpdate = Body(...),
) -> EmployeePersonalInformationResponse:
    return EMPLOYEE_PERSONAL_INFORMATION_SERVICE.upsert(
        db, employee_id=employee_id, request=payload
    )


@employee_personal_information_router.patch(
    "/employees/{employee_id}/personal-information",
    response_model=EmployeePersonalInformationResponse,
    summary="Partial update personal information (nested route)",
)
def patch_nested_personal_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    payload: EmployeePersonalInformationUpdate = Body(...),
) -> EmployeePersonalInformationResponse:
    return EMPLOYEE_PERSONAL_INFORMATION_SERVICE.update(
        db, employee_id=employee_id, request=payload
    )


@employee_personal_information_router.delete(
    "/employees/{employee_id}/personal-information",
    response_model=EmployeePersonalInformationDeleteResponse,
    summary="Delete personal information (nested route)",
)
def delete_nested_personal_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
) -> EmployeePersonalInformationDeleteResponse:
    return EMPLOYEE_PERSONAL_INFORMATION_SERVICE.delete(db, employee_id=employee_id)


# ============================================================================
# Routes for organization employee personal information
# ============================================================================

@employee_personal_information_router.get(
    "/organizations/{organization_id}/employee-personal-information",
    response_model=EmployeePersonalInformationListResponse,
    summary="List employee personal information by organization ID",
)
def list_organization_personal_information(
    *,
    db: Session = Depends(get_db),
    organization_id: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=1000, description="Max number of records to return"),
    search: Optional[str] = Query(None, description="Search query by name, email, phone, city, etc."),
) -> EmployeePersonalInformationListResponse:
    """
    Retrieve paginated employee personal information records belonging to a specific organization.
    """
    return EMPLOYEE_PERSONAL_INFORMATION_SERVICE.get_by_organization_id(
        db, organization_id=organization_id, skip=skip, limit=limit, search=search
    )


@employee_personal_information_router.get(
    "/employee-personal-information/organization/{organization_id}",
    response_model=EmployeePersonalInformationListResponse,
    summary="List employee personal information by organization ID (alt route)",
)
def list_employee_personal_information_by_organization(
    *,
    db: Session = Depends(get_db),
    organization_id: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=1000, description="Max number of records to return"),
    search: Optional[str] = Query(None, description="Search query by name, email, phone, city, etc."),
) -> EmployeePersonalInformationListResponse:
    """
    Retrieve paginated employee personal information records belonging to a specific organization.
    """
    return EMPLOYEE_PERSONAL_INFORMATION_SERVICE.get_by_organization_id(
        db, organization_id=organization_id, skip=skip, limit=limit, search=search
    )

