import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Name of the organization")
    slug: Optional[str] = Field(None, max_length=255, description="Unique slug for the organization")
    email: Optional[str] = Field(None, max_length=255, description="Organization contact email")
    phone: Optional[str] = Field(None, max_length=50, description="Organization contact phone")
    address: Optional[str] = Field(None, description="Physical address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State/Province")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal/ZIP code")
    status: Optional[str] = Field("active", max_length=30, description="Organization status (active/inactive)")

    model_config = ConfigDict(from_attributes=True)


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Name of the organization")
    slug: Optional[str] = Field(None, max_length=255, description="Unique slug; auto-generated if omitted")
    email: Optional[str] = Field(None, max_length=255, description="Organization contact email")
    phone: Optional[str] = Field(None, max_length=50, description="Organization contact phone")
    address: Optional[str] = Field(None, description="Physical address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State/Province")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal/ZIP code")
    status: Optional[str] = Field("active", max_length=30, description="Initial status")

    model_config = ConfigDict(from_attributes=True)


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Name of the organization")
    slug: Optional[str] = Field(None, max_length=255, description="Unique slug")
    email: Optional[str] = Field(None, max_length=255, description="Organization contact email")
    phone: Optional[str] = Field(None, max_length=50, description="Organization contact phone")
    address: Optional[str] = Field(None, description="Physical address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State/Province")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal/ZIP code")
    status: Optional[str] = Field(None, max_length=30, description="Organization status")

    model_config = ConfigDict(from_attributes=True)


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationListResponse(BaseModel):
    organizations: List[OrganizationResponse] = []
    total: int = 0

    model_config = ConfigDict(from_attributes=True)


class OrganizationSummaryResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: Optional[str] = None
    status: str = "active"
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    total_users: int = 0
    active_users: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationDeactivateResponse(BaseModel):
    message: str = "Organization deactivated successfully"
    success: bool = True
    id: str
    status: str = "inactive"

    model_config = ConfigDict(from_attributes=True)
