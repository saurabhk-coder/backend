import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class OrganizationSettingBase(BaseModel):
    setting_key: str = Field(..., max_length=255, description="Configuration setting key")
    setting_value: Optional[str] = Field(None, description="Configuration setting value")

    model_config = ConfigDict(from_attributes=True)


class OrganizationSettingCreateOrUpdate(BaseModel):
    setting_value: Optional[str] = Field(None, description="Configuration setting value")

    model_config = ConfigDict(from_attributes=True)


class OrganizationSettingResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    setting_key: str
    setting_value: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationSettingListResponse(BaseModel):
    settings: List[OrganizationSettingResponse] = []
    total: int = 0

    model_config = ConfigDict(from_attributes=True)


class OrganizationSettingDeleteResponse(BaseModel):
    message: str = "Setting deleted successfully"
    success: bool = True
    setting_key: str

    model_config = ConfigDict(from_attributes=True)
