from typing import Optional
from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.orm import Session

from ....schemas.employee_department_information import (
    EmployeeDepartmentInformationBase,
    EmployeeDepartmentInformationCreate,
    EmployeeDepartmentInformationDeleteResponse,
    EmployeeDepartmentInformationListResponse,
    EmployeeDepartmentInformationResponse,
    EmployeeDepartmentInformationUpdate,
)
from ....services.employee_department_information_service import (
    EMPLOYEE_DEPARTMENT_INFORMATION_SERVICE,
)
from ...deps import get_db

employee_department_information_router = APIRouter()


@employee_department_information_router.post(
    "/employee-department-information",
    response_model=EmployeeDepartmentInformationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create employee department information",
)
def create_department_information(
    *,
    db: Session = Depends(get_db),
    payload: EmployeeDepartmentInformationCreate = Body(...),
) -> EmployeeDepartmentInformationResponse:
    """
    Create a new department information record for an employee.
    """
    return EMPLOYEE_DEPARTMENT_INFORMATION_SERVICE.create(db, request=payload)


@employee_department_information_router.get(
    "/employee-department-information",
    response_model=EmployeeDepartmentInformationListResponse,
    summary="List employee department information records",
)
def list_department_information(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=1000, description="Max number of records to return"),
    search: Optional[str] = Query(None, description="Search by department, designation, location, mode, or type"),
) -> EmployeeDepartmentInformationListResponse:
    """
    Retrieve paginated employee department information records with optional search filter.
    """
    return EMPLOYEE_DEPARTMENT_INFORMATION_SERVICE.get_multi(
        db, skip=skip, limit=limit, search=search
    )


@employee_department_information_router.get(
    "/employee-department-information/{employee_id}",
    response_model=EmployeeDepartmentInformationResponse,
    summary="Get employee department information by employee ID",
)
def get_department_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
) -> EmployeeDepartmentInformationResponse:
    """
    Retrieve department information for a specific employee by employee_id.
    """
    return EMPLOYEE_DEPARTMENT_INFORMATION_SERVICE.get_by_employee_id(
        db, employee_id=employee_id
    )


@employee_department_information_router.put(
    "/employee-department-information/{employee_id}",
    response_model=EmployeeDepartmentInformationResponse,
    summary="Upsert or full update employee department information",
)
def upsert_department_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    payload: EmployeeDepartmentInformationUpdate = Body(...),
) -> EmployeeDepartmentInformationResponse:
    """
    Create or update department information for a given employee_id (upsert).
    """
    return EMPLOYEE_DEPARTMENT_INFORMATION_SERVICE.upsert(
        db, employee_id=employee_id, request=payload
    )


@employee_department_information_router.patch(
    "/employee-department-information/{employee_id}",
    response_model=EmployeeDepartmentInformationResponse,
    summary="Partial update employee department information",
)
def patch_department_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    payload: EmployeeDepartmentInformationUpdate = Body(...),
) -> EmployeeDepartmentInformationResponse:
    """
    Partially update department information fields for a specific employee.
    """
    return EMPLOYEE_DEPARTMENT_INFORMATION_SERVICE.update(
        db, employee_id=employee_id, request=payload
    )


@employee_department_information_router.delete(
    "/employee-department-information/{employee_id}",
    response_model=EmployeeDepartmentInformationDeleteResponse,
    summary="Delete employee department information",
)
def delete_department_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
) -> EmployeeDepartmentInformationDeleteResponse:
    """
    Delete department information for a specific employee.
    """
    return EMPLOYEE_DEPARTMENT_INFORMATION_SERVICE.delete(db, employee_id=employee_id)


# ============================================================================
# Nested routes for convenience: /employees/{employee_id}/department-information
# ============================================================================

@employee_department_information_router.get(
    "/employees/{employee_id}/department-information",
    response_model=EmployeeDepartmentInformationResponse,
    summary="Get department information (nested route)",
)
def get_nested_department_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
) -> EmployeeDepartmentInformationResponse:
    return EMPLOYEE_DEPARTMENT_INFORMATION_SERVICE.get_by_employee_id(
        db, employee_id=employee_id
    )


@employee_department_information_router.post(
    "/employees/{employee_id}/department-information",
    response_model=EmployeeDepartmentInformationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create department information (nested route)",
)
def create_nested_department_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    payload: EmployeeDepartmentInformationBase = Body(...),
) -> EmployeeDepartmentInformationResponse:
    create_schema = EmployeeDepartmentInformationCreate(
        employee_id=employee_id,
        **payload.model_dump(),
    )
    return EMPLOYEE_DEPARTMENT_INFORMATION_SERVICE.create(db, request=create_schema)


@employee_department_information_router.put(
    "/employees/{employee_id}/department-information",
    response_model=EmployeeDepartmentInformationResponse,
    summary="Upsert department information (nested route)",
)
def upsert_nested_department_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    payload: EmployeeDepartmentInformationUpdate = Body(...),
) -> EmployeeDepartmentInformationResponse:
    return EMPLOYEE_DEPARTMENT_INFORMATION_SERVICE.upsert(
        db, employee_id=employee_id, request=payload
    )


@employee_department_information_router.patch(
    "/employees/{employee_id}/department-information",
    response_model=EmployeeDepartmentInformationResponse,
    summary="Partial update department information (nested route)",
)
def patch_nested_department_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    payload: EmployeeDepartmentInformationUpdate = Body(...),
) -> EmployeeDepartmentInformationResponse:
    return EMPLOYEE_DEPARTMENT_INFORMATION_SERVICE.update(
        db, employee_id=employee_id, request=payload
    )


@employee_department_information_router.delete(
    "/employees/{employee_id}/department-information",
    response_model=EmployeeDepartmentInformationDeleteResponse,
    summary="Delete department information (nested route)",
)
def delete_nested_department_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
) -> EmployeeDepartmentInformationDeleteResponse:
    return EMPLOYEE_DEPARTMENT_INFORMATION_SERVICE.delete(db, employee_id=employee_id)
