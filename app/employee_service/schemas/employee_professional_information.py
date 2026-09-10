from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EmployeeProfessionalInformationBase(BaseModel):
    tenth_roll: Optional[str] = Field(None, max_length=100, description="10th class roll number")
    tenth_percentage_cgpa: Optional[str] = Field(None, max_length=20, description="10th class percentage or CGPA")
    twelfth_roll: Optional[str] = Field(None, max_length=100, description="12th class roll number")
    twelfth_percentage_cgpa: Optional[str] = Field(None, max_length=20, description="12th class percentage or CGPA")
    graduation_roll: Optional[str] = Field(None, max_length=100, description="Graduation roll number")
    graduation_percentage_cgpa: Optional[str] = Field(None, max_length=20, description="Graduation percentage or CGPA")
    post_graduation_roll: Optional[str] = Field(None, max_length=100, description="Post-graduation roll number")
    post_graduation_percentage_cgpa: Optional[str] = Field(None, max_length=20, description="Post-graduation percentage or CGPA")
    total_experience_years: Optional[Decimal] = Field(None, description="Total experience in years")
    last_company_details: Optional[str] = Field(None, max_length=255, description="Previous company details")
    last_ctc: Optional[Decimal] = Field(None, description="Last drawn CTC amount")
    certifications: Optional[str] = Field(None, description="Certifications details")
    skills: Optional[str] = Field(None, description="Skills and technical competencies")

    model_config = ConfigDict(from_attributes=True)


class EmployeeProfessionalInformationCreate(EmployeeProfessionalInformationBase):
    employee_id: int = Field(..., description="Employee ID foreign key reference")


class EmployeeProfessionalInformationUpdate(BaseModel):
    tenth_roll: Optional[str] = Field(None, max_length=100, description="10th class roll number")
    tenth_percentage_cgpa: Optional[str] = Field(None, max_length=20, description="10th class percentage or CGPA")
    twelfth_roll: Optional[str] = Field(None, max_length=100, description="12th class roll number")
    twelfth_percentage_cgpa: Optional[str] = Field(None, max_length=20, description="12th class percentage or CGPA")
    graduation_roll: Optional[str] = Field(None, max_length=100, description="Graduation roll number")
    graduation_percentage_cgpa: Optional[str] = Field(None, max_length=20, description="Graduation percentage or CGPA")
    post_graduation_roll: Optional[str] = Field(None, max_length=100, description="Post-graduation roll number")
    post_graduation_percentage_cgpa: Optional[str] = Field(None, max_length=20, description="Post-graduation percentage or CGPA")
    total_experience_years: Optional[Decimal] = Field(None, description="Total experience in years")
    last_company_details: Optional[str] = Field(None, max_length=255, description="Previous company details")
    last_ctc: Optional[Decimal] = Field(None, description="Last drawn CTC amount")
    certifications: Optional[str] = Field(None, description="Certifications details")
    skills: Optional[str] = Field(None, description="Skills and technical competencies")

    model_config = ConfigDict(from_attributes=True)


class EmployeeProfessionalInformationResponse(EmployeeProfessionalInformationBase):
    employee_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EmployeeProfessionalInformationListResponse(BaseModel):
    items: List[EmployeeProfessionalInformationResponse] = []
    total: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 1

    model_config = ConfigDict(from_attributes=True)


class EmployeeProfessionalInformationDeleteResponse(BaseModel):
    message: str = "Employee professional information deleted successfully"
    success: bool = True
    employee_id: int

    model_config = ConfigDict(from_attributes=True)
