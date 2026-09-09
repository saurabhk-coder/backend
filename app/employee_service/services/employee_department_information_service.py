from abc import ABC, abstractmethod
import math
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..crud.crud_employee_department_information import (
    CRUD_EMPLOYEE_DEPARTMENT_INFORMATION,
)
from ..schemas.employee_department_information import (
    EmployeeDepartmentInformationCreate,
    EmployeeDepartmentInformationDeleteResponse,
    EmployeeDepartmentInformationListResponse,
    EmployeeDepartmentInformationResponse,
    EmployeeDepartmentInformationUpdate,
)


class IEmployeeDepartmentInformationService(ABC):
    @abstractmethod
    def create(
        self, db: Session, request: EmployeeDepartmentInformationCreate
    ) -> EmployeeDepartmentInformationResponse:
        pass

    @abstractmethod
    def get_by_employee_id(
        self, db: Session, employee_id: int
    ) -> EmployeeDepartmentInformationResponse:
        pass

    @abstractmethod
    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> EmployeeDepartmentInformationListResponse:
        pass

    @abstractmethod
    def update(
        self,
        db: Session,
        employee_id: int,
        request: EmployeeDepartmentInformationUpdate,
    ) -> EmployeeDepartmentInformationResponse:
        pass

    @abstractmethod
    def upsert(
        self,
        db: Session,
        employee_id: int,
        request: Union[EmployeeDepartmentInformationCreate, EmployeeDepartmentInformationUpdate, Dict[str, Any]],
    ) -> EmployeeDepartmentInformationResponse:
        pass

    @abstractmethod
    def delete(
        self, db: Session, employee_id: int
    ) -> EmployeeDepartmentInformationDeleteResponse:
        pass


class EmployeeDepartmentInformationService(IEmployeeDepartmentInformationService):
    def create(
        self, db: Session, request: EmployeeDepartmentInformationCreate
    ) -> EmployeeDepartmentInformationResponse:
        existing = CRUD_EMPLOYEE_DEPARTMENT_INFORMATION.get(db, employee_id=request.employee_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Employee department information already exists for employee_id '{request.employee_id}'",
            )
        record = CRUD_EMPLOYEE_DEPARTMENT_INFORMATION.create(db, obj_in=request)
        return EmployeeDepartmentInformationResponse.model_validate(record)

    def get_by_employee_id(
        self, db: Session, employee_id: int
    ) -> EmployeeDepartmentInformationResponse:
        record = CRUD_EMPLOYEE_DEPARTMENT_INFORMATION.get(db, employee_id=employee_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee department information not found for employee_id '{employee_id}'",
            )
        return EmployeeDepartmentInformationResponse.model_validate(record)

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> EmployeeDepartmentInformationListResponse:
        items = CRUD_EMPLOYEE_DEPARTMENT_INFORMATION.get_multi(
            db, skip=skip, limit=limit, search=search
        )
        total = CRUD_EMPLOYEE_DEPARTMENT_INFORMATION.count(db, search=search)
        page = (skip // limit) + 1 if limit > 0 else 1
        total_pages = max(1, math.ceil(total / limit)) if limit > 0 else 1

        return EmployeeDepartmentInformationListResponse(
            items=[EmployeeDepartmentInformationResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages,
        )

    def update(
        self,
        db: Session,
        employee_id: int,
        request: EmployeeDepartmentInformationUpdate,
    ) -> EmployeeDepartmentInformationResponse:
        record = CRUD_EMPLOYEE_DEPARTMENT_INFORMATION.get(db, employee_id=employee_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee department information not found for employee_id '{employee_id}'",
            )
        updated = CRUD_EMPLOYEE_DEPARTMENT_INFORMATION.update(db, db_obj=record, obj_in=request)
        return EmployeeDepartmentInformationResponse.model_validate(updated)

    def upsert(
        self,
        db: Session,
        employee_id: int,
        request: Union[EmployeeDepartmentInformationCreate, EmployeeDepartmentInformationUpdate, Dict[str, Any]],
    ) -> EmployeeDepartmentInformationResponse:
        record = CRUD_EMPLOYEE_DEPARTMENT_INFORMATION.create_or_update(
            db, employee_id=employee_id, obj_in=request
        )
        return EmployeeDepartmentInformationResponse.model_validate(record)

    def delete(
        self, db: Session, employee_id: int
    ) -> EmployeeDepartmentInformationDeleteResponse:
        record = CRUD_EMPLOYEE_DEPARTMENT_INFORMATION.get(db, employee_id=employee_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee department information not found for employee_id '{employee_id}'",
            )
        CRUD_EMPLOYEE_DEPARTMENT_INFORMATION.remove(db, employee_id=employee_id)
        return EmployeeDepartmentInformationDeleteResponse(
            message="Employee department information deleted successfully",
            success=True,
            employee_id=employee_id,
        )


EMPLOYEE_DEPARTMENT_INFORMATION_SERVICE: IEmployeeDepartmentInformationService = (
    EmployeeDepartmentInformationService()
)
