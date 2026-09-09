from abc import ABC, abstractmethod
import math
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..crud.crud_employee_account_details import (
    CRUD_EMPLOYEE_ACCOUNT_DETAILS,
)
from ..schemas.employee_account_details import (
    EmployeeAccountDetailsCreate,
    EmployeeAccountDetailsDeleteResponse,
    EmployeeAccountDetailsListResponse,
    EmployeeAccountDetailsResponse,
    EmployeeAccountDetailsUpdate,
)


class IEmployeeAccountDetailsService(ABC):
    @abstractmethod
    def create(
        self, db: Session, request: EmployeeAccountDetailsCreate
    ) -> EmployeeAccountDetailsResponse:
        pass

    @abstractmethod
    def get_by_employee_id(
        self, db: Session, employee_id: int
    ) -> EmployeeAccountDetailsResponse:
        pass

    @abstractmethod
    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> EmployeeAccountDetailsListResponse:
        pass

    @abstractmethod
    def update(
        self,
        db: Session,
        employee_id: int,
        request: EmployeeAccountDetailsUpdate,
    ) -> EmployeeAccountDetailsResponse:
        pass

    @abstractmethod
    def upsert(
        self,
        db: Session,
        employee_id: int,
        request: Union[EmployeeAccountDetailsCreate, EmployeeAccountDetailsUpdate, Dict[str, Any]],
    ) -> EmployeeAccountDetailsResponse:
        pass

    @abstractmethod
    def delete(
        self, db: Session, employee_id: int
    ) -> EmployeeAccountDetailsDeleteResponse:
        pass


class EmployeeAccountDetailsService(IEmployeeAccountDetailsService):
    def create(
        self, db: Session, request: EmployeeAccountDetailsCreate
    ) -> EmployeeAccountDetailsResponse:
        existing = CRUD_EMPLOYEE_ACCOUNT_DETAILS.get(db, employee_id=request.employee_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Employee account details already exist for employee_id '{request.employee_id}'",
            )
        record = CRUD_EMPLOYEE_ACCOUNT_DETAILS.create(db, obj_in=request)
        return EmployeeAccountDetailsResponse.model_validate(record)

    def get_by_employee_id(
        self, db: Session, employee_id: int
    ) -> EmployeeAccountDetailsResponse:
        record = CRUD_EMPLOYEE_ACCOUNT_DETAILS.get(db, employee_id=employee_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee account details not found for employee_id '{employee_id}'",
            )
        return EmployeeAccountDetailsResponse.model_validate(record)

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> EmployeeAccountDetailsListResponse:
        items = CRUD_EMPLOYEE_ACCOUNT_DETAILS.get_multi(
            db, skip=skip, limit=limit, search=search
        )
        total = CRUD_EMPLOYEE_ACCOUNT_DETAILS.count(db, search=search)
        page = (skip // limit) + 1 if limit > 0 else 1
        total_pages = max(1, math.ceil(total / limit)) if limit > 0 else 1

        return EmployeeAccountDetailsListResponse(
            items=[EmployeeAccountDetailsResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages,
        )

    def update(
        self,
        db: Session,
        employee_id: int,
        request: EmployeeAccountDetailsUpdate,
    ) -> EmployeeAccountDetailsResponse:
        record = CRUD_EMPLOYEE_ACCOUNT_DETAILS.get(db, employee_id=employee_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee account details not found for employee_id '{employee_id}'",
            )
        updated = CRUD_EMPLOYEE_ACCOUNT_DETAILS.update(db, db_obj=record, obj_in=request)
        return EmployeeAccountDetailsResponse.model_validate(updated)

    def upsert(
        self,
        db: Session,
        employee_id: int,
        request: Union[EmployeeAccountDetailsCreate, EmployeeAccountDetailsUpdate, Dict[str, Any]],
    ) -> EmployeeAccountDetailsResponse:
        record = CRUD_EMPLOYEE_ACCOUNT_DETAILS.create_or_update(
            db, employee_id=employee_id, obj_in=request
        )
        return EmployeeAccountDetailsResponse.model_validate(record)

    def delete(
        self, db: Session, employee_id: int
    ) -> EmployeeAccountDetailsDeleteResponse:
        record = CRUD_EMPLOYEE_ACCOUNT_DETAILS.get(db, employee_id=employee_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee account details not found for employee_id '{employee_id}'",
            )
        CRUD_EMPLOYEE_ACCOUNT_DETAILS.remove(db, employee_id=employee_id)
        return EmployeeAccountDetailsDeleteResponse(
            message="Employee account details deleted successfully",
            success=True,
            employee_id=employee_id,
        )


EMPLOYEE_ACCOUNT_DETAILS_SERVICE: IEmployeeAccountDetailsService = (
    EmployeeAccountDetailsService()
)
