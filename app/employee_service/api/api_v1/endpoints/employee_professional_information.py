from typing import Optional
from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.orm import Session

from ....schemas.employee_professional_information import (
    EmployeeProfessionalInformationBase,
    EmployeeProfessionalInformationCreate,
    EmployeeProfessionalInformationDeleteResponse,
    EmployeeProfessionalInformationListResponse,
    EmployeeProfessionalInformationResponse,
    EmployeeProfessionalInformationUpdate,
)
from ....services.employee_professional_information_service import (
    EMPLOYEE_PROFESSIONAL_INFORMATION_SERVICE,
)
from ...deps import get_db

employee_professional_information_router = APIRouter()


@employee_professional_information_router.post(
    "/employee-professional-information",
    response_model=EmployeeProfessionalInformationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create employee professional information",
)
def create_professional_information(
    *,
    db: Session = Depends(get_db),
    payload: EmployeeProfessionalInformationCreate = Body(...),
) -> EmployeeProfessionalInformationResponse:
    """
    Create a new professional information record for an employee.
    """
    return EMPLOYEE_PROFESSIONAL_INFORMATION_SERVICE.create(db, request=payload)


@employee_professional_information_router.get(
    "/employee-professional-information",
    response_model=EmployeeProfessionalInformationListResponse,
    summary="List employee professional information records",
)
def list_professional_information(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=1000, description="Max number of records to return"),
    search: Optional[str] = Query(
        None,
        description="Search by roll numbers, company, certifications, or skills",
    ),
) -> EmployeeProfessionalInformationListResponse:
    """
    Retrieve paginated employee professional information records with optional search filter.
    """
    return EMPLOYEE_PROFESSIONAL_INFORMATION_SERVICE.get_multi(
        db, skip=skip, limit=limit, search=search
    )


@employee_professional_information_router.get(
    "/employee-professional-information/{employee_id}",
    response_model=EmployeeProfessionalInformationResponse,
    summary="Get employee professional information by employee ID",
)
def get_professional_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
) -> EmployeeProfessionalInformationResponse:
    """
    Retrieve professional information for a specific employee by employee_id.
    """
    return EMPLOYEE_PROFESSIONAL_INFORMATION_SERVICE.get_by_employee_id(
        db, employee_id=employee_id
    )


@employee_professional_information_router.put(
    "/employee-professional-information/{employee_id}",
    response_model=EmployeeProfessionalInformationResponse,
    summary="Upsert or full update employee professional information",
)
def upsert_professional_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    payload: EmployeeProfessionalInformationUpdate = Body(...),
) -> EmployeeProfessionalInformationResponse:
    """
    Create or update professional information for a given employee_id (upsert).
    """
    return EMPLOYEE_PROFESSIONAL_INFORMATION_SERVICE.upsert(
        db, employee_id=employee_id, request=payload
    )


@employee_professional_information_router.patch(
    "/employee-professional-information/{employee_id}",
    response_model=EmployeeProfessionalInformationResponse,
    summary="Partial update employee professional information",
)
def patch_professional_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    payload: EmployeeProfessionalInformationUpdate = Body(...),
) -> EmployeeProfessionalInformationResponse:
    """
    Partially update professional information fields for a specific employee.
    """
    return EMPLOYEE_PROFESSIONAL_INFORMATION_SERVICE.update(
        db, employee_id=employee_id, request=payload
    )


@employee_professional_information_router.delete(
    "/employee-professional-information/{employee_id}",
    response_model=EmployeeProfessionalInformationDeleteResponse,
    summary="Delete employee professional information",
)
def delete_professional_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
) -> EmployeeProfessionalInformationDeleteResponse:
    """
    Delete professional information for a specific employee.
    """
    return EMPLOYEE_PROFESSIONAL_INFORMATION_SERVICE.delete(
        db, employee_id=employee_id
    )


# ============================================================================
# Nested routes for convenience: /employees/{employee_id}/professional-information
# ============================================================================

@employee_professional_information_router.get(
    "/employees/{employee_id}/professional-information",
    response_model=EmployeeProfessionalInformationResponse,
    summary="Get professional information (nested route)",
)
def get_nested_professional_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
) -> EmployeeProfessionalInformationResponse:
    return EMPLOYEE_PROFESSIONAL_INFORMATION_SERVICE.get_by_employee_id(
        db, employee_id=employee_id
    )


@employee_professional_information_router.post(
    "/employees/{employee_id}/professional-information",
    response_model=EmployeeProfessionalInformationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create professional information (nested route)",
)
def create_nested_professional_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    payload: EmployeeProfessionalInformationBase = Body(...),
) -> EmployeeProfessionalInformationResponse:
    create_schema = EmployeeProfessionalInformationCreate(
        employee_id=employee_id,
        **payload.model_dump(),
    )
    return EMPLOYEE_PROFESSIONAL_INFORMATION_SERVICE.create(
        db, request=create_schema
    )


@employee_professional_information_router.put(
    "/employees/{employee_id}/professional-information",
    response_model=EmployeeProfessionalInformationResponse,
    summary="Upsert professional information (nested route)",
)
def upsert_nested_professional_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    payload: EmployeeProfessionalInformationUpdate = Body(...),
) -> EmployeeProfessionalInformationResponse:
    return EMPLOYEE_PROFESSIONAL_INFORMATION_SERVICE.upsert(
        db, employee_id=employee_id, request=payload
    )


@employee_professional_information_router.patch(
    "/employees/{employee_id}/professional-information",
    response_model=EmployeeProfessionalInformationResponse,
    summary="Partial update professional information (nested route)",
)
def patch_nested_professional_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    payload: EmployeeProfessionalInformationUpdate = Body(...),
) -> EmployeeProfessionalInformationResponse:
    return EMPLOYEE_PROFESSIONAL_INFORMATION_SERVICE.update(
        db, employee_id=employee_id, request=payload
    )


@employee_professional_information_router.delete(
    "/employees/{employee_id}/professional-information",
    response_model=EmployeeProfessionalInformationDeleteResponse,
    summary="Delete professional information (nested route)",
)
def delete_nested_professional_information(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
) -> EmployeeProfessionalInformationDeleteResponse:
    return EMPLOYEE_PROFESSIONAL_INFORMATION_SERVICE.delete(
        db, employee_id=employee_id
    )
