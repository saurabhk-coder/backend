from abc import ABC, abstractmethod
import math
import uuid
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..crud.crud_employee_personal_information import (
    CRUD_EMPLOYEE_PERSONAL_INFORMATION,
)
from ..schemas.employee_personal_information import (
    EmployeePersonalInformationCreate,
    EmployeePersonalInformationDeleteResponse,
    EmployeePersonalInformationListResponse,
    EmployeePersonalInformationResponse,
    EmployeePersonalInformationUpdate,
)


class IEmployeePersonalInformationService(ABC):
    @abstractmethod
    def create(
        self, db: Session, request: EmployeePersonalInformationCreate
    ) -> EmployeePersonalInformationResponse:
        pass

    @abstractmethod
    def get_by_employee_id(
        self, db: Session, employee_id: int
    ) -> EmployeePersonalInformationResponse:
        pass

    @abstractmethod
    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> EmployeePersonalInformationListResponse:
        pass

    @abstractmethod
    def get_by_organization_id(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> EmployeePersonalInformationListResponse:
        pass

    @abstractmethod
    def update(
        self,
        db: Session,
        employee_id: int,
        request: EmployeePersonalInformationUpdate,
    ) -> EmployeePersonalInformationResponse:
        pass

    @abstractmethod
    def upsert(
        self,
        db: Session,
        employee_id: int,
        request: Union[EmployeePersonalInformationCreate, EmployeePersonalInformationUpdate, Dict[str, Any]],
    ) -> EmployeePersonalInformationResponse:
        pass

    @abstractmethod
    def delete(
        self, db: Session, employee_id: int
    ) -> EmployeePersonalInformationDeleteResponse:
        pass


class EmployeePersonalInformationService(IEmployeePersonalInformationService):
    def create(
        self, db: Session, request: EmployeePersonalInformationCreate
    ) -> EmployeePersonalInformationResponse:
        existing = CRUD_EMPLOYEE_PERSONAL_INFORMATION.get(db, employee_id=request.employee_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Employee personal information already exists for employee_id '{request.employee_id}'",
            )
        record = CRUD_EMPLOYEE_PERSONAL_INFORMATION.create(db, obj_in=request)
        return EmployeePersonalInformationResponse.model_validate(record)

    def get_by_employee_id(
        self, db: Session, employee_id: int
    ) -> EmployeePersonalInformationResponse:
        record = CRUD_EMPLOYEE_PERSONAL_INFORMATION.get(db, employee_id=employee_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee personal information not found for employee_id '{employee_id}'",
            )
        return EmployeePersonalInformationResponse.model_validate(record)

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> EmployeePersonalInformationListResponse:
        items = CRUD_EMPLOYEE_PERSONAL_INFORMATION.get_multi(
            db, skip=skip, limit=limit, search=search, organization_id=organization_id
        )
        total = CRUD_EMPLOYEE_PERSONAL_INFORMATION.count(
            db, search=search, organization_id=organization_id
        )
        page = (skip // limit) + 1 if limit > 0 else 1
        total_pages = max(1, math.ceil(total / limit)) if limit > 0 else 1

        return EmployeePersonalInformationListResponse(
            items=[EmployeePersonalInformationResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages,
        )

    def get_by_organization_id(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> EmployeePersonalInformationListResponse:
        return self.get_multi(
            db, skip=skip, limit=limit, search=search, organization_id=organization_id
        )

    def update(
        self,
        db: Session,
        employee_id: int,
        request: EmployeePersonalInformationUpdate,
    ) -> EmployeePersonalInformationResponse:
        record = CRUD_EMPLOYEE_PERSONAL_INFORMATION.get(db, employee_id=employee_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee personal information not found for employee_id '{employee_id}'",
            )
        updated = CRUD_EMPLOYEE_PERSONAL_INFORMATION.update(db, db_obj=record, obj_in=request)
        return EmployeePersonalInformationResponse.model_validate(updated)

    def upsert(
        self,
        db: Session,
        employee_id: int,
        request: Union[EmployeePersonalInformationCreate, EmployeePersonalInformationUpdate, Dict[str, Any]],
    ) -> EmployeePersonalInformationResponse:
        record = CRUD_EMPLOYEE_PERSONAL_INFORMATION.create_or_update(
            db, employee_id=employee_id, obj_in=request
        )
        return EmployeePersonalInformationResponse.model_validate(record)

    def delete(
        self, db: Session, employee_id: int
    ) -> EmployeePersonalInformationDeleteResponse:
        record = CRUD_EMPLOYEE_PERSONAL_INFORMATION.get(db, employee_id=employee_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee personal information not found for employee_id '{employee_id}'",
            )
        CRUD_EMPLOYEE_PERSONAL_INFORMATION.remove(db, employee_id=employee_id)
        return EmployeePersonalInformationDeleteResponse(
            message="Employee personal information deleted successfully",
            success=True,
            employee_id=employee_id,
        )


EMPLOYEE_PERSONAL_INFORMATION_SERVICE: IEmployeePersonalInformationService = (
    EmployeePersonalInformationService()
)
