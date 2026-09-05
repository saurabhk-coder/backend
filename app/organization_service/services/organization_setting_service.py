import uuid
from abc import ABC, abstractmethod
from typing import List, Optional, Union
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..crud.crud_organization import CRUD_ORGANIZATION
from ..crud.crud_organization_setting import CRUD_ORGANIZATION_SETTING
from ..models.organization_setting import OrganizationSettingDb
from ..schemas.organization_setting import (
    OrganizationSettingDeleteResponse,
    OrganizationSettingListResponse,
    OrganizationSettingResponse,
)


class IOrganizationSettingService(ABC):
    @abstractmethod
    def get_settings(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        skip: int = 0,
        limit: int = 100,
    ) -> List[OrganizationSettingResponse]:
        pass

    @abstractmethod
    def get_setting(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        setting_key: str,
    ) -> OrganizationSettingResponse:
        pass

    @abstractmethod
    def set_setting(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        setting_key: str,
        setting_value: Optional[str],
    ) -> OrganizationSettingResponse:
        pass

    @abstractmethod
    def delete_setting(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        setting_key: str,
    ) -> OrganizationSettingDeleteResponse:
        pass


class OrganizationSettingService(IOrganizationSettingService):
    def _verify_organization_exists(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
    ):
        org = CRUD_ORGANIZATION.get(db, id=organization_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization with id '{organization_id}' not found",
            )
        return org

    def get_settings(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        skip: int = 0,
        limit: int = 100,
    ) -> List[OrganizationSettingResponse]:
        self._verify_organization_exists(db, organization_id)
        settings = CRUD_ORGANIZATION_SETTING.get_multi(
            db, organization_id=organization_id, skip=skip, limit=limit
        )
        return [OrganizationSettingResponse.model_validate(s) for s in settings]

    def get_setting(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        setting_key: str,
    ) -> OrganizationSettingResponse:
        self._verify_organization_exists(db, organization_id)
        setting = CRUD_ORGANIZATION_SETTING.get(
            db, organization_id=organization_id, setting_key=setting_key
        )
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting with key '{setting_key}' not found",
            )
        return OrganizationSettingResponse.model_validate(setting)

    def set_setting(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        setting_key: str,
        setting_value: Optional[str],
    ) -> OrganizationSettingResponse:
        self._verify_organization_exists(db, organization_id)
        setting = CRUD_ORGANIZATION_SETTING.create_or_update(
            db,
            organization_id=organization_id,
            setting_key=setting_key,
            setting_value=setting_value,
        )
        return OrganizationSettingResponse.model_validate(setting)

    def delete_setting(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        setting_key: str,
    ) -> OrganizationSettingDeleteResponse:
        self._verify_organization_exists(db, organization_id)
        setting = CRUD_ORGANIZATION_SETTING.get(
            db, organization_id=organization_id, setting_key=setting_key
        )
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting with key '{setting_key}' not found",
            )
        CRUD_ORGANIZATION_SETTING.remove(
            db, organization_id=organization_id, setting_key=setting_key
        )
        return OrganizationSettingDeleteResponse(
            message="Setting deleted successfully",
            success=True,
            setting_key=setting_key,
        )


ORGANIZATION_SETTING_SERVICE: IOrganizationSettingService = OrganizationSettingService()
