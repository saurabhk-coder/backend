import uuid
from datetime import datetime
from typing import Any, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the role")
    description: Optional[str] = Field(None, description="Detailed description of the role")
    permissions_json: Optional[Any] = Field(default_factory=dict, description="Role permissions stored as JSON")

    model_config = ConfigDict(from_attributes=True)


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the role")
    description: Optional[str] = Field(None, description="Detailed description of the role")
    permissions_json: Optional[Any] = Field(default=None, description="Permissions data (dict, list, or JSON structure)")

    model_config = ConfigDict(from_attributes=True)


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Name of the role")
    description: Optional[str] = Field(None, description="Detailed description of the role")
    permissions_json: Optional[Any] = Field(None, description="Permissions data (dict, list, or JSON structure)")

    model_config = ConfigDict(from_attributes=True)


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    permissions_json: Optional[Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RoleListResponse(BaseModel):
    roles: List[RoleResponse] = []
    total: int = 0

    model_config = ConfigDict(from_attributes=True)


class RolePermissionsUpdate(BaseModel):
    permissions: Optional[Any] = Field(None, description="Permissions payload")
    permissions_json: Optional[Any] = Field(None, description="Permissions payload under permissions_json key")

    model_config = ConfigDict(from_attributes=True)


class RolePermissionsResponse(BaseModel):
    role_id: uuid.UUID
    role_name: str
    permissions: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)


class RoleDeleteResponse(BaseModel):
    message: str = "Role deleted successfully"
    success: bool = True
    id: str

    model_config = ConfigDict(from_attributes=True)
