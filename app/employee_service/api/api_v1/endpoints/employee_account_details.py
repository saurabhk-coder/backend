from typing import Optional
from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.orm import Session

from ....schemas.employee_account_details import (
    EmployeeAccountDetailsBase,
    EmployeeAccountDetailsCreate,
    EmployeeAccountDetailsDeleteResponse,
    EmployeeAccountDetailsListResponse,
    EmployeeAccountDetailsResponse,
    EmployeeAccountDetailsUpdate,
)
from ....services.employee_account_details_service import (
    EMPLOYEE_ACCOUNT_DETAILS_SERVICE,
)
from ...deps import get_db

employee_account_details_router = APIRouter()


@employee_account_details_router.post(
    "/employee-account-details",
    response_model=EmployeeAccountDetailsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create employee account details",
)
def create_account_details(
    *,
    db: Session = Depends(get_db),
    payload: EmployeeAccountDetailsCreate = Body(...),
) -> EmployeeAccountDetailsResponse:
    """
    Create a new account details record for an employee.
    """
    return EMPLOYEE_ACCOUNT_DETAILS_SERVICE.create(db, request=payload)


@employee_account_details_router.get(
    "/employee-account-details",
    response_model=EmployeeAccountDetailsListResponse,
    summary="List employee account details records",
)
def list_account_details(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=1000, description="Max number of records to return"),
    search: Optional[str] = Query(None, description="Search by bank name, IFSC, or account number"),
) -> EmployeeAccountDetailsListResponse:
    """
    Retrieve paginated employee account details records with optional search filter.
    """
    return EMPLOYEE_ACCOUNT_DETAILS_SERVICE.get_multi(
        db, skip=skip, limit=limit, search=search
    )


@employee_account_details_router.get(
    "/employee-account-details/{employee_id}",
    response_model=EmployeeAccountDetailsResponse,
    summary="Get employee account details by employee ID",
)
def get_account_details(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
) -> EmployeeAccountDetailsResponse:
    """
    Retrieve account details for a specific employee by employee_id.
    """
    return EMPLOYEE_ACCOUNT_DETAILS_SERVICE.get_by_employee_id(
        db, employee_id=employee_id
    )


@employee_account_details_router.put(
    "/employee-account-details/{employee_id}",
    response_model=EmployeeAccountDetailsResponse,
    summary="Upsert or full update employee account details",
)
def upsert_account_details(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    payload: EmployeeAccountDetailsUpdate = Body(...),
) -> EmployeeAccountDetailsResponse:
    """
    Create or update account details for a given employee_id (upsert).
    """
    return EMPLOYEE_ACCOUNT_DETAILS_SERVICE.upsert(
        db, employee_id=employee_id, request=payload
    )


@employee_account_details_router.patch(
    "/employee-account-details/{employee_id}",
    response_model=EmployeeAccountDetailsResponse,
    summary="Partial update employee account details",
)
def patch_account_details(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    payload: EmployeeAccountDetailsUpdate = Body(...),
) -> EmployeeAccountDetailsResponse:
    """
    Partially update account details fields for a specific employee.
    """
    return EMPLOYEE_ACCOUNT_DETAILS_SERVICE.update(
        db, employee_id=employee_id, request=payload
    )


@employee_account_details_router.delete(
    "/employee-account-details/{employee_id}",
    response_model=EmployeeAccountDetailsDeleteResponse,
    summary="Delete employee account details",
)
def delete_account_details(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
) -> EmployeeAccountDetailsDeleteResponse:
    """
    Delete account details for a specific employee.
    """
    return EMPLOYEE_ACCOUNT_DETAILS_SERVICE.delete(db, employee_id=employee_id)


# ============================================================================
# Nested routes for convenience: /employees/{employee_id}/account-details
# ============================================================================

@employee_account_details_router.get(
    "/employees/{employee_id}/account-details",
    response_model=EmployeeAccountDetailsResponse,
    summary="Get account details (nested route)",
)
def get_nested_account_details(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
) -> EmployeeAccountDetailsResponse:
    return EMPLOYEE_ACCOUNT_DETAILS_SERVICE.get_by_employee_id(
        db, employee_id=employee_id
    )


@employee_account_details_router.post(
    "/employees/{employee_id}/account-details",
    response_model=EmployeeAccountDetailsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create account details (nested route)",
)
def create_nested_account_details(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    payload: EmployeeAccountDetailsBase = Body(...),
) -> EmployeeAccountDetailsResponse:
    create_schema = EmployeeAccountDetailsCreate(
        employee_id=employee_id,
        **payload.model_dump(),
    )
    return EMPLOYEE_ACCOUNT_DETAILS_SERVICE.create(db, request=create_schema)


@employee_account_details_router.put(
    "/employees/{employee_id}/account-details",
    response_model=EmployeeAccountDetailsResponse,
    summary="Upsert account details (nested route)",
)
def upsert_nested_account_details(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    payload: EmployeeAccountDetailsUpdate = Body(...),
) -> EmployeeAccountDetailsResponse:
    return EMPLOYEE_ACCOUNT_DETAILS_SERVICE.upsert(
        db, employee_id=employee_id, request=payload
    )


@employee_account_details_router.patch(
    "/employees/{employee_id}/account-details",
    response_model=EmployeeAccountDetailsResponse,
    summary="Partial update account details (nested route)",
)
def patch_nested_account_details(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    payload: EmployeeAccountDetailsUpdate = Body(...),
) -> EmployeeAccountDetailsResponse:
    return EMPLOYEE_ACCOUNT_DETAILS_SERVICE.update(
        db, employee_id=employee_id, request=payload
    )


@employee_account_details_router.delete(
    "/employees/{employee_id}/account-details",
    response_model=EmployeeAccountDetailsDeleteResponse,
    summary="Delete account details (nested route)",
)
def delete_nested_account_details(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
) -> EmployeeAccountDetailsDeleteResponse:
    return EMPLOYEE_ACCOUNT_DETAILS_SERVICE.delete(db, employee_id=employee_id)
