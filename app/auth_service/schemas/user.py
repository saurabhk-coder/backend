from typing import Optional
from pydantic import BaseModel, EmailStr



class UserBase(BaseModel):
    id :str=""
    email: Optional[EmailStr] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    countryCode: Optional[str] = None
    is_active: Optional[bool] = True
    
    class Config:
        orm_mode = True

class AddFiledRequest(BaseModel):
    file_size:str=""
    folder_name:str=""
    content_type:str =""
    file_name:str =""
    container_name:str=""
    file_extension:str=""
    file_location:str=""
    file_url:str=""
    user_id:str=""
    account_id:str=""
    display_name:str=""

class FileUploadRequest(BaseModel):
    file_size:str=""
    content_type:str =""
    file_name:str =""
    container_name:str=""
    file_extension:str=""
    file_key:str=""
    user_id:str=""
    account_id:str=""
    


class UserCreate(UserBase):
    email: EmailStr
    password: str



