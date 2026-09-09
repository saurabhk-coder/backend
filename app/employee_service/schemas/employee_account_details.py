from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EmployeeAccountDetailsBase(BaseModel):
    bank_name: Optional[str] = Field(None, max_length=150, description="Name of the bank")
    ifsc_code: Optional[str] = Field(None, max_length=20, description="Bank IFSC / routing code")
    account_number: Optional[str] = Field(None, max_length=50, description="Bank account number")

    model_config = ConfigDict(from_attributes=True)


class EmployeeAccountDetailsCreate(EmployeeAccountDetailsBase):
    employee_id: int = Field(..., description="Employee ID foreign key reference")


class EmployeeAccountDetailsUpdate(BaseModel):
    bank_name: Optional[str] = Field(None, max_length=150, description="Name of the bank")
    ifsc_code: Optional[str] = Field(None, max_length=20, description="Bank IFSC / routing code")
    account_number: Optional[str] = Field(None, max_length=50, description="Bank account number")

    model_config = ConfigDict(from_attributes=True)


class EmployeeAccountDetailsResponse(EmployeeAccountDetailsBase):
    employee_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EmployeeAccountDetailsListResponse(BaseModel):
    items: List[EmployeeAccountDetailsResponse] = []
    total: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 1

    model_config = ConfigDict(from_attributes=True)


class EmployeeAccountDetailsDeleteResponse(BaseModel):
    message: str = "Employee account details deleted successfully"
    success: bool = True
    employee_id: int

    model_config = ConfigDict(from_attributes=True)
