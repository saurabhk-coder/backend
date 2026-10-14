import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EmployeeDocumentBase(BaseModel):
    employee_id: int = Field(..., description="Employee ID foreign key reference")
    organization_id: Optional[uuid.UUID] = Field(None, description="Organization ID")
    file_name: str = Field(..., min_length=1, max_length=255, description="Original filename")
    file_title: Optional[str] = Field(None, max_length=255, description="Document display title / label")
    file_category: str = Field(
        "document",
        description="Category: govt_id_proof, profile_photo, resume, contract, certificate, tax_document, other",
    )
    content_type: Optional[str] = Field(None, max_length=100, description="MIME content type")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    file_extension: Optional[str] = Field(None, max_length=20, description="File extension, e.g. .pdf, .jpg")
    gcs_bucket: str = Field("hrms-aaralia", description="GCS bucket name")
    gcs_blob_name: str = Field(..., description="Path within GCS bucket")
    file_url: Optional[str] = Field(None, description="Public or storage URL")
    uploaded_by: Optional[uuid.UUID] = Field(None, description="User ID of uploader")
    description: Optional[str] = Field(None, description="Optional description or notes")

    model_config = ConfigDict(from_attributes=True)


class EmployeeDocumentCreate(EmployeeDocumentBase):
    pass


class EmployeeDocumentUpdate(BaseModel):
    file_title: Optional[str] = Field(None, max_length=255, description="Document display title / label")
    file_category: Optional[str] = Field(None, description="Document category")
    description: Optional[str] = Field(None, description="Optional description or notes")

    model_config = ConfigDict(from_attributes=True)


class EmployeeDocumentResponse(EmployeeDocumentBase):
    id: uuid.UUID
    download_url: Optional[str] = Field(None, description="Signed or direct download URL")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EmployeeDocumentListResponse(BaseModel):
    items: List[EmployeeDocumentResponse] = []
    total: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 1
    employee_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class EmployeeDocumentDeleteResponse(BaseModel):
    message: str = "Employee document deleted successfully"
    success: bool = True
    document_id: str

    model_config = ConfigDict(from_attributes=True)


class DocumentCategoryItem(BaseModel):
    id: str
    label: str
    description: str
