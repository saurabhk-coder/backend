from abc import ABC, abstractmethod
import math
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..crud.crud_employee_professional_information import (
    CRUD_EMPLOYEE_PROFESSIONAL_INFORMATION,
)
from ..schemas.employee_professional_information import (
    EmployeeProfessionalInformationCreate,
    EmployeeProfessionalInformationDeleteResponse,
    EmployeeProfessionalInformationListResponse,
    EmployeeProfessionalInformationResponse,
    EmployeeProfessionalInformationUpdate,
)


class IEmployeeProfessionalInformationService(ABC):
    @abstractmethod
    def create(
        self, db: Session, request: EmployeeProfessionalInformationCreate
    ) -> EmployeeProfessionalInformationResponse:
        pass

    @abstractmethod
    def get_by_employee_id(
        self, db: Session, employee_id: int
    ) -> EmployeeProfessionalInformationResponse:
        pass

    @abstractmethod
    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> EmployeeProfessionalInformationListResponse:
        pass

    @abstractmethod
    def update(
        self,
        db: Session,
        employee_id: int,
        request: EmployeeProfessionalInformationUpdate,
    ) -> EmployeeProfessionalInformationResponse:
        pass

    @abstractmethod
    def upsert(
        self,
        db: Session,
        employee_id: int,
        request: Union[
            EmployeeProfessionalInformationCreate,
            EmployeeProfessionalInformationUpdate,
            Dict[str, Any],
        ],
    ) -> EmployeeProfessionalInformationResponse:
        pass

    @abstractmethod
    def delete(
        self, db: Session, employee_id: int
    ) -> EmployeeProfessionalInformationDeleteResponse:
        pass


class EmployeeProfessionalInformationService(
    IEmployeeProfessionalInformationService
):
    def create(
        self, db: Session, request: EmployeeProfessionalInformationCreate
    ) -> EmployeeProfessionalInformationResponse:
        existing = CRUD_EMPLOYEE_PROFESSIONAL_INFORMATION.get(
            db, employee_id=request.employee_id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Employee professional information already exists for employee_id '{request.employee_id}'",
            )
        record = CRUD_EMPLOYEE_PROFESSIONAL_INFORMATION.create(
            db, obj_in=request
        )
        return EmployeeProfessionalInformationResponse.model_validate(record)

    def get_by_employee_id(
        self, db: Session, employee_id: int
    ) -> EmployeeProfessionalInformationResponse:
        record = CRUD_EMPLOYEE_PROFESSIONAL_INFORMATION.get(
            db, employee_id=employee_id
        )
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee professional information not found for employee_id '{employee_id}'",
            )
        return EmployeeProfessionalInformationResponse.model_validate(record)

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> EmployeeProfessionalInformationListResponse:
        items = CRUD_EMPLOYEE_PROFESSIONAL_INFORMATION.get_multi(
            db, skip=skip, limit=limit, search=search
        )
        total = CRUD_EMPLOYEE_PROFESSIONAL_INFORMATION.count(db, search=search)
        page = (skip // limit) + 1 if limit > 0 else 1
        total_pages = max(1, math.ceil(total / limit)) if limit > 0 else 1

        return EmployeeProfessionalInformationListResponse(
            items=[
                EmployeeProfessionalInformationResponse.model_validate(item)
                for item in items
            ],
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages,
        )

    def update(
        self,
        db: Session,
        employee_id: int,
        request: EmployeeProfessionalInformationUpdate,
    ) -> EmployeeProfessionalInformationResponse:
        record = CRUD_EMPLOYEE_PROFESSIONAL_INFORMATION.get(
            db, employee_id=employee_id
        )
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee professional information not found for employee_id '{employee_id}'",
            )
        updated = CRUD_EMPLOYEE_PROFESSIONAL_INFORMATION.update(
            db, db_obj=record, obj_in=request
        )
        return EmployeeProfessionalInformationResponse.model_validate(updated)

    def upsert(
        self,
        db: Session,
        employee_id: int,
        request: Union[
            EmployeeProfessionalInformationCreate,
            EmployeeProfessionalInformationUpdate,
            Dict[str, Any],
        ],
    ) -> EmployeeProfessionalInformationResponse:
        record = CRUD_EMPLOYEE_PROFESSIONAL_INFORMATION.create_or_update(
            db, employee_id=employee_id, obj_in=request
        )
        return EmployeeProfessionalInformationResponse.model_validate(record)

    def delete(
        self, db: Session, employee_id: int
    ) -> EmployeeProfessionalInformationDeleteResponse:
        record = CRUD_EMPLOYEE_PROFESSIONAL_INFORMATION.get(
            db, employee_id=employee_id
        )
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee professional information not found for employee_id '{employee_id}'",
            )
        CRUD_EMPLOYEE_PROFESSIONAL_INFORMATION.remove(
            db, employee_id=employee_id
        )
        return EmployeeProfessionalInformationDeleteResponse(
            message="Employee professional information deleted successfully",
            success=True,
            employee_id=employee_id,
        )


EMPLOYEE_PROFESSIONAL_INFORMATION_SERVICE: IEmployeeProfessionalInformationService = (
    EmployeeProfessionalInformationService()
)
