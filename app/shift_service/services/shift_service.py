import uuid
from abc import ABC, abstractmethod
from typing import Optional, Union
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.organization_service.crud.crud_organization import CRUD_ORGANIZATION
from ..crud.crud_shift import CRUD_SHIFT
from ..schemas.shift import (
    PaginationInfo,
    ShiftCreate,
    ShiftDeleteResponse,
    ShiftListResponse,
    ShiftResponse,
    ShiftUpdate,
)


class IShiftService(ABC):
    @abstractmethod
    def list_shifts(
        self,
        db: Session,
        *,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
        search: Optional[str] = None,
        department: Optional[str] = None,
        location: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ShiftListResponse:
        pass

    @abstractmethod
    def get_shift(
        self,
        db: Session,
        *,
        id: Union[uuid.UUID, str],
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> ShiftResponse:
        pass

    @abstractmethod
    def create_shift(
        self,
        db: Session,
        *,
        organization_id: Union[uuid.UUID, str],
        obj_in: ShiftCreate,
    ) -> ShiftResponse:
        pass

    @abstractmethod
    def update_shift(
        self,
        db: Session,
        *,
        id: Union[uuid.UUID, str],
        obj_in: ShiftUpdate,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> ShiftResponse:
        pass

    @abstractmethod
    def delete_shift(
        self,
        db: Session,
        *,
        id: Union[uuid.UUID, str],
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> ShiftDeleteResponse:
        pass


class ShiftService(IShiftService):
    def _verify_organization_exists(
        self, db: Session, organization_id: Union[uuid.UUID, str]
    ) -> None:
        org = CRUD_ORGANIZATION.get(db, id=organization_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization with id '{organization_id}' not found",
            )

    def list_shifts(
        self,
        db: Session,
        *,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
        search: Optional[str] = None,
        department: Optional[str] = None,
        location: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ShiftListResponse:
        if organization_id:
            self._verify_organization_exists(db, organization_id)

        skip = max(0, (page - 1) * page_size)
        shifts, total = CRUD_SHIFT.get_multi(
            db,
            organization_id=organization_id,
            search=search,
            department=department,
            location=location,
            is_active=is_active,
            skip=skip,
            limit=page_size,
        )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        data = [CRUD_SHIFT.to_schema(s) for s in shifts]

        return ShiftListResponse(
            success=True,
            data=data,
            pagination=PaginationInfo(
                page=page,
                pageSize=page_size,
                total=total,
                totalPages=total_pages,
            ),
        )

    def get_shift(
        self,
        db: Session,
        *,
        id: Union[uuid.UUID, str],
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> ShiftResponse:
        if organization_id:
            self._verify_organization_exists(db, organization_id)

        shift = CRUD_SHIFT.get(db, id=id, organization_id=organization_id)
        if not shift:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shift with id '{id}' not found",
            )
        return CRUD_SHIFT.to_schema(shift)

    def create_shift(
        self,
        db: Session,
        *,
        organization_id: Union[uuid.UUID, str],
        obj_in: ShiftCreate,
    ) -> ShiftResponse:
        self._verify_organization_exists(db, organization_id)
        shift = CRUD_SHIFT.create(db, organization_id=organization_id, obj_in=obj_in)
        return CRUD_SHIFT.to_schema(shift)

    def update_shift(
        self,
        db: Session,
        *,
        id: Union[uuid.UUID, str],
        obj_in: ShiftUpdate,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> ShiftResponse:
        if organization_id:
            self._verify_organization_exists(db, organization_id)

        shift = CRUD_SHIFT.get(db, id=id, organization_id=organization_id)
        if not shift:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shift with id '{id}' not found",
            )
        updated = CRUD_SHIFT.update(db, db_obj=shift, obj_in=obj_in)
        return CRUD_SHIFT.to_schema(updated)

    def delete_shift(
        self,
        db: Session,
        *,
        id: Union[uuid.UUID, str],
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> ShiftDeleteResponse:
        if organization_id:
            self._verify_organization_exists(db, organization_id)

        shift = CRUD_SHIFT.get(db, id=id, organization_id=organization_id)
        if not shift:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shift with id '{id}' not found",
            )
        CRUD_SHIFT.remove(db, db_obj=shift)
        return ShiftDeleteResponse(success=True, message="Shift deleted successfully")


SHIFT_SERVICE = ShiftService()
