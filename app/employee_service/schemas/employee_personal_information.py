from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EmployeePersonalInformationBase(BaseModel):
    profile_photo: Optional[str] = Field(None, description="Profile photo URL or base64 string")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    mobile_number: Optional[str] = Field(None, max_length=20, description="Mobile phone number")
    email: Optional[str] = Field(None, max_length=255, description="Personal or work email address")
    father_name: Optional[str] = Field(None, max_length=150, description="Father's name")
    mother_name: Optional[str] = Field(None, max_length=150, description="Mother's name")
    marital_status: Optional[str] = Field(None, max_length=30, description="Marital status (Single, Married, etc.)")
    spouse_name: Optional[str] = Field(None, max_length=150, description="Spouse's name if applicable")
    emergency_contact: Optional[str] = Field(None, max_length=20, description="Emergency contact phone number")
    date_of_birth: Optional[date] = Field(None, description="Date of birth (YYYY-MM-DD)")
    govt_id_proof: Optional[str] = Field(None, max_length=50, description="Government ID type (e.g. Passport, PAN, Aadhaar)")
    id_proof_number: Optional[str] = Field(None, max_length=100, description="Government ID document number")
    gender: Optional[str] = Field(None, max_length=30, description="Gender")
    nationality: Optional[str] = Field(None, max_length=100, description="Nationality")
    address: Optional[str] = Field(None, description="Residential street address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State / Province")
    zip_code: Optional[str] = Field(None, max_length=20, description="Postal / ZIP code")

    model_config = ConfigDict(from_attributes=True)


class EmployeePersonalInformationCreate(EmployeePersonalInformationBase):
    employee_id: int = Field(..., description="Employee ID foreign key reference")


class EmployeePersonalInformationUpdate(BaseModel):
    profile_photo: Optional[str] = Field(None, description="Profile photo URL or base64 string")
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    mobile_number: Optional[str] = Field(None, max_length=20, description="Mobile phone number")
    email: Optional[str] = Field(None, max_length=255, description="Personal or work email address")
    father_name: Optional[str] = Field(None, max_length=150, description="Father's name")
    mother_name: Optional[str] = Field(None, max_length=150, description="Mother's name")
    marital_status: Optional[str] = Field(None, max_length=30, description="Marital status (Single, Married, etc.)")
    spouse_name: Optional[str] = Field(None, max_length=150, description="Spouse's name if applicable")
    emergency_contact: Optional[str] = Field(None, max_length=20, description="Emergency contact phone number")
    date_of_birth: Optional[date] = Field(None, description="Date of birth (YYYY-MM-DD)")
    govt_id_proof: Optional[str] = Field(None, max_length=50, description="Government ID type")
    id_proof_number: Optional[str] = Field(None, max_length=100, description="Government ID document number")
    gender: Optional[str] = Field(None, max_length=30, description="Gender")
    nationality: Optional[str] = Field(None, max_length=100, description="Nationality")
    address: Optional[str] = Field(None, description="Residential street address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State / Province")
    zip_code: Optional[str] = Field(None, max_length=20, description="Postal / ZIP code")

    model_config = ConfigDict(from_attributes=True)


class EmployeePersonalInformationResponse(EmployeePersonalInformationBase):
    employee_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EmployeePersonalInformationListResponse(BaseModel):
    items: List[EmployeePersonalInformationResponse] = []
    total: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 1

    model_config = ConfigDict(from_attributes=True)


class EmployeePersonalInformationDeleteResponse(BaseModel):
    message: str = "Employee personal information deleted successfully"
    success: bool = True
    employee_id: int

    model_config = ConfigDict(from_attributes=True)
