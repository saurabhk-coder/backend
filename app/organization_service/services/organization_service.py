import uuid
from abc import ABC, abstractmethod
from typing import List, Optional, Union
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..crud.crud_organization import CRUD_ORGANIZATION
from ..models.organization import OrganizationDb
from ..schemas.organization import (
    OrganizationCreate,
    OrganizationDeactivateResponse,
    OrganizationListResponse,
    OrganizationResponse,
    OrganizationSummaryResponse,
    OrganizationUpdate,
)


class IOrganizationService(ABC):
    @abstractmethod
    def create_organization(
        self,
        db: Session,
        request: OrganizationCreate,
    ) -> OrganizationResponse:
        pass

    @abstractmethod
    def get_organizations(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[OrganizationResponse]:
        pass

    @abstractmethod
    def get_organization_by_id(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
    ) -> OrganizationResponse:
        pass

    @abstractmethod
    def update_organization(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        request: OrganizationUpdate,
    ) -> OrganizationResponse:
        pass

    @abstractmethod
    def deactivate_organization(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
    ) -> OrganizationDeactivateResponse:
        pass

    @abstractmethod
    def get_summary(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
    ) -> OrganizationSummaryResponse:
        pass


class OrganizationService(IOrganizationService):
    def create_organization(
        self,
        db: Session,
        request: OrganizationCreate,
    ) -> OrganizationResponse:
        existing = CRUD_ORGANIZATION.get_by_name(db, request.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Organization with name '{request.name}' already exists",
            )
        org = CRUD_ORGANIZATION.create(db, obj_in=request)
        return OrganizationResponse.model_validate(org)

    def get_organizations(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[OrganizationResponse]:
        orgs = CRUD_ORGANIZATION.get_multi(
            db, skip=skip, limit=limit, search=search, status=status
        )
        return [OrganizationResponse.model_validate(o) for o in orgs]

    def get_organization_by_id(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
    ) -> OrganizationResponse:
        org = CRUD_ORGANIZATION.get(db, id=organization_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization with id '{organization_id}' not found",
            )
        return OrganizationResponse.model_validate(org)

    def update_organization(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
        request: OrganizationUpdate,
    ) -> OrganizationResponse:
        org = CRUD_ORGANIZATION.get(db, id=organization_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization with id '{organization_id}' not found",
            )

        if request.name and request.name.strip().lower() != org.name.lower():
            existing = CRUD_ORGANIZATION.get_by_name(db, request.name)
            if existing and existing.id != org.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Organization with name '{request.name}' already exists",
                )

        if request.slug and request.slug.strip().lower() != (org.slug or "").lower():
            existing_slug = CRUD_ORGANIZATION.get_by_slug(db, request.slug)
            if existing_slug and existing_slug.id != org.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Organization with slug '{request.slug}' already exists",
                )

        updated = CRUD_ORGANIZATION.update(db, db_obj=org, obj_in=request)
        return OrganizationResponse.model_validate(updated)

    def deactivate_organization(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
    ) -> OrganizationDeactivateResponse:
        org = CRUD_ORGANIZATION.get(db, id=organization_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization with id '{organization_id}' not found",
            )
        deactivated = CRUD_ORGANIZATION.deactivate(db, db_obj=org)
        return OrganizationDeactivateResponse(
            message="Organization deactivated successfully",
            success=True,
            id=str(deactivated.id),
            status=deactivated.status,
        )

    def get_summary(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
    ) -> OrganizationSummaryResponse:
        org = CRUD_ORGANIZATION.get(db, id=organization_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization with id '{organization_id}' not found",
            )

        total_users, active_users = CRUD_ORGANIZATION.get_user_counts(db, org.id)
        return OrganizationSummaryResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            status=org.status,
            email=org.email,
            phone=org.phone,
            city=org.city,
            state=org.state,
            country=org.country,
            total_users=total_users,
            active_users=active_users,
            created_at=org.created_at,
            updated_at=org.updated_at,
        )


ORGANIZATION_SERVICE: IOrganizationService = OrganizationService()
