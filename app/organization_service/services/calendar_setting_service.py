import uuid
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Union
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..crud.crud_calendar_setting import CRUD_CALENDAR_SETTING
from ..crud.crud_organization import CRUD_ORGANIZATION
from ..models.calendar_setting import CalendarSettingDb
from ..schemas.calendar_setting import (
    CalendarSettingCreate,
    CalendarSettingData,
    CalendarSettingDeleteResponse,
    CalendarSettingListResponse,
    CalendarSettingSingleResponse,
    CalendarSettingUpdate,
)


class ICalendarSettingService(ABC):
    @abstractmethod
    def list_calendar_settings(
        self,
        db: Session,
        *,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
        location: Optional[str] = None,
        is_default: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> CalendarSettingListResponse:
        pass

    @abstractmethod
    def get_calendar_setting(
        self,
        db: Session,
        *,
        identifier: Union[uuid.UUID, str],
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> CalendarSettingSingleResponse:
        pass

    @abstractmethod
    def create_or_upsert_calendar_setting(
        self,
        db: Session,
        *,
        organization_id: Union[uuid.UUID, str],
        obj_in: CalendarSettingCreate,
    ) -> Tuple[CalendarSettingSingleResponse, bool]:
        pass

    @abstractmethod
    def update_calendar_setting(
        self,
        db: Session,
        *,
        identifier: Union[uuid.UUID, str],
        obj_in: CalendarSettingUpdate,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> CalendarSettingSingleResponse:
        pass

    @abstractmethod
    def delete_calendar_setting(
        self,
        db: Session,
        *,
        identifier: Union[uuid.UUID, str],
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> CalendarSettingDeleteResponse:
        pass


class CalendarSettingService(ICalendarSettingService):
    def _verify_organization_exists(
        self, db: Session, organization_id: Union[uuid.UUID, str]
    ) -> None:
        org = CRUD_ORGANIZATION.get(db, id=organization_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization with id '{organization_id}' not found",
            )

    def list_calendar_settings(
        self,
        db: Session,
        *,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
        location: Optional[str] = None,
        is_default: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> CalendarSettingListResponse:
        if organization_id:
            self._verify_organization_exists(db, organization_id)

        settings = CRUD_CALENDAR_SETTING.get_multi(
            db,
            organization_id=organization_id,
            location=location,
            is_default=is_default,
            skip=skip,
            limit=limit,
        )
        data = [CRUD_CALENDAR_SETTING.to_schema(s) for s in settings]
        return CalendarSettingListResponse(success=True, data=data)


    def get_calendar_setting(
        self,
        db: Session,
        *,
        identifier: Union[uuid.UUID, str],
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> CalendarSettingSingleResponse:
        if organization_id:
            self._verify_organization_exists(db, organization_id)

        setting = CRUD_CALENDAR_SETTING.get_by_id_or_location(
            db,
            identifier=identifier,
            organization_id=organization_id,
        )
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Calendar setting '{identifier}' not found",
            )

        data = CRUD_CALENDAR_SETTING.to_schema(setting)
        return CalendarSettingSingleResponse(success=True, data=data)

    def create_or_upsert_calendar_setting(
        self,
        db: Session,
        *,
        organization_id: Union[uuid.UUID, str],
        obj_in: CalendarSettingCreate,
    ) -> Tuple[CalendarSettingSingleResponse, bool]:
        self._verify_organization_exists(db, organization_id)

        db_obj, is_new = CRUD_CALENDAR_SETTING.create_or_upsert(
            db,
            organization_id=organization_id,
            obj_in=obj_in,
        )
        data = CRUD_CALENDAR_SETTING.to_schema(db_obj)
        return CalendarSettingSingleResponse(success=True, data=data), is_new

    def update_calendar_setting(
        self,
        db: Session,
        *,
        identifier: Union[uuid.UUID, str],
        obj_in: CalendarSettingUpdate,
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> CalendarSettingSingleResponse:
        if organization_id:
            self._verify_organization_exists(db, organization_id)

        setting = CRUD_CALENDAR_SETTING.get_by_id_or_location(
            db,
            identifier=identifier,
            organization_id=organization_id,
        )
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Calendar setting '{identifier}' not found",
            )

        updated = CRUD_CALENDAR_SETTING.update(db, db_obj=setting, obj_in=obj_in)
        data = CRUD_CALENDAR_SETTING.to_schema(updated)
        return CalendarSettingSingleResponse(success=True, data=data)

    def delete_calendar_setting(
        self,
        db: Session,
        *,
        identifier: Union[uuid.UUID, str],
        organization_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> CalendarSettingDeleteResponse:
        if organization_id:
            self._verify_organization_exists(db, organization_id)

        setting = CRUD_CALENDAR_SETTING.get_by_id_or_location(
            db,
            identifier=identifier,
            organization_id=organization_id,
        )
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Calendar setting '{identifier}' not found",
            )

        setting_id = setting.id
        setting_location = setting.location
        CRUD_CALENDAR_SETTING.remove(db, db_obj=setting)

        return CalendarSettingDeleteResponse(
            success=True,
            message="Calendar setting removed successfully (fallback to organization default)",
            id=setting_id,
            location=setting_location,
        )


CALENDAR_SETTING_SERVICE = CalendarSettingService()
