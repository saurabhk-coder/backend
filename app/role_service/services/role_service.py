import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..crud.crud_role import CRUD_ROLE
from ..models.role import RoleDb
from ..schemas.role import (
    RoleCreate,
    RoleDeleteResponse,
    RoleListResponse,
    RolePermissionsResponse,
    RolePermissionsUpdate,
    RoleResponse,
    RoleUpdate,
)


class IRoleService(ABC):
    @abstractmethod
    def create_role(self, db: Session, request: RoleCreate) -> RoleResponse:
        pass

    @abstractmethod
    def get_roles(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> List[RoleResponse]:
        pass

    @abstractmethod
    def get_role_by_id(self, db: Session, role_id: Union[uuid.UUID, str]) -> RoleResponse:
        pass

    @abstractmethod
    def update_role(
        self,
        db: Session,
        role_id: Union[uuid.UUID, str],
        request: RoleUpdate,
    ) -> RoleResponse:
        pass

    @abstractmethod
    def delete_role(self, db: Session, role_id: Union[uuid.UUID, str]) -> RoleDeleteResponse:
        pass

    @abstractmethod
    def get_permissions(self, db: Session, role_id: Union[uuid.UUID, str]) -> RolePermissionsResponse:
        pass

    @abstractmethod
    def replace_permissions(
        self,
        db: Session,
        role_id: Union[uuid.UUID, str],
        permissions_data: Any,
    ) -> RolePermissionsResponse:
        pass


class RoleService(IRoleService):
    def create_role(self, db: Session, request: RoleCreate) -> RoleResponse:
        existing = CRUD_ROLE.get_by_name(db, request.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with name '{request.name}' already exists",
            )
        role = CRUD_ROLE.create(db, obj_in=request)
        return RoleResponse.model_validate(role)

    def get_roles(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> List[RoleResponse]:
        roles = CRUD_ROLE.get_multi(db, skip=skip, limit=limit, search=search)
        return [RoleResponse.model_validate(r) for r in roles]

    def get_role_by_id(self, db: Session, role_id: Union[uuid.UUID, str]) -> RoleResponse:
        role = CRUD_ROLE.get(db, id=role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with id '{role_id}' not found",
            )
        return RoleResponse.model_validate(role)

    def update_role(
        self,
        db: Session,
        role_id: Union[uuid.UUID, str],
        request: RoleUpdate,
    ) -> RoleResponse:
        role = CRUD_ROLE.get(db, id=role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with id '{role_id}' not found",
            )

        if request.name and request.name.strip().lower() != role.name.lower():
            existing = CRUD_ROLE.get_by_name(db, request.name)
            if existing and existing.id != role.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Role with name '{request.name}' already exists",
                )

        updated = CRUD_ROLE.update(db, db_obj=role, obj_in=request)
        return RoleResponse.model_validate(updated)

    def delete_role(self, db: Session, role_id: Union[uuid.UUID, str]) -> RoleDeleteResponse:
        role = CRUD_ROLE.get(db, id=role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with id '{role_id}' not found",
            )
        CRUD_ROLE.remove(db, id=role.id)
        return RoleDeleteResponse(
            message="Role deleted successfully",
            success=True,
            id=str(role.id),
        )

    def get_permissions(self, db: Session, role_id: Union[uuid.UUID, str]) -> RolePermissionsResponse:
        role = CRUD_ROLE.get(db, id=role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with id '{role_id}' not found",
            )
        return RolePermissionsResponse(
            role_id=role.id,
            role_name=role.name,
            permissions=role.permissions_json,
        )

    def replace_permissions(
        self,
        db: Session,
        role_id: Union[uuid.UUID, str],
        permissions_data: Any,
    ) -> RolePermissionsResponse:
        role = CRUD_ROLE.get(db, id=role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with id '{role_id}' not found",
            )

        # Handle different input representations
        extracted_permissions = permissions_data
        if isinstance(permissions_data, RolePermissionsUpdate):
            if permissions_data.permissions is not None:
                extracted_permissions = permissions_data.permissions
            elif permissions_data.permissions_json is not None:
                extracted_permissions = permissions_data.permissions_json
            else:
                extracted_permissions = {}
        elif isinstance(permissions_data, dict):
            if "permissions" in permissions_data and len(permissions_data) <= 2:
                extracted_permissions = permissions_data["permissions"]
            elif "permissions_json" in permissions_data and len(permissions_data) <= 2:
                extracted_permissions = permissions_data["permissions_json"]

        updated = CRUD_ROLE.update_permissions(db, db_obj=role, permissions=extracted_permissions)
        return RolePermissionsResponse(
            role_id=updated.id,
            role_name=updated.name,
            permissions=updated.permissions_json,
        )


ROLE_SERVICE: IRoleService = RoleService()
