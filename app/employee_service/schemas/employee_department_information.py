from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EmployeeDepartmentInformationBase(BaseModel):
    department: Optional[str] = Field(None, max_length=150, description="Department name")
    designation: Optional[str] = Field(None, max_length=150, description="Job designation / title")
    reporting_manager_id: Optional[int] = Field(None, description="Employee ID of reporting manager")
    work_location: Optional[str] = Field(None, max_length=150, description="Office / work location")
    work_mode: Optional[str] = Field(None, max_length=50, description="Work mode (e.g. Remote, Onsite, Hybrid)")
    employment_type: Optional[str] = Field(None, max_length=50, description="Employment type (e.g. Full-time, Part-time, Contract)")
    ctc_offered: Optional[Decimal] = Field(None, description="Offered CTC amount")

    model_config = ConfigDict(from_attributes=True)


class EmployeeDepartmentInformationCreate(EmployeeDepartmentInformationBase):
    employee_id: int = Field(..., description="Employee ID foreign key reference")


class EmployeeDepartmentInformationUpdate(BaseModel):
    department: Optional[str] = Field(None, max_length=150, description="Department name")
    designation: Optional[str] = Field(None, max_length=150, description="Job designation / title")
    reporting_manager_id: Optional[int] = Field(None, description="Employee ID of reporting manager")
    work_location: Optional[str] = Field(None, max_length=150, description="Office / work location")
    work_mode: Optional[str] = Field(None, max_length=50, description="Work mode")
    employment_type: Optional[str] = Field(None, max_length=50, description="Employment type")
    ctc_offered: Optional[Decimal] = Field(None, description="Offered CTC amount")

    model_config = ConfigDict(from_attributes=True)


class EmployeeDepartmentInformationResponse(EmployeeDepartmentInformationBase):
    employee_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EmployeeDepartmentInformationListResponse(BaseModel):
    items: List[EmployeeDepartmentInformationResponse] = []
    total: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 1

    model_config = ConfigDict(from_attributes=True)


class EmployeeDepartmentInformationDeleteResponse(BaseModel):
    message: str = "Employee department information deleted successfully"
    success: bool = True
    employee_id: int

    model_config = ConfigDict(from_attributes=True)
