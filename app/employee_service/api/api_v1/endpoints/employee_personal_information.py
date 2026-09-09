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
    summary="Create employee personal information",
)
def create_personal_information(
    *,
    db: Session = Depends(get_db),
    payload: EmployeePersonalInformationCreate = Body(...),
) -> EmployeePersonalInformationResponse:
    """
    Create a new personal information record for an employee.
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
) -> EmployeePersonalInformationListResponse:
    """
    Retrieve paginated employee personal information records with optional search filter.
    """
    return EMPLOYEE_PERSONAL_INFORMATION_SERVICE.get_multi(
        db, skip=skip, limit=limit, search=search
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
    payload: EmployeePersonalInformationBase = Body(...),
) -> EmployeePersonalInformationResponse:
    create_schema = EmployeePersonalInformationCreate(
        employee_id=employee_id,
        **payload.model_dump(),
    )
    return EMPLOYEE_PERSONAL_INFORMATION_SERVICE.create(db, request=create_schema)


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
