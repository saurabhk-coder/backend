from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional,List

from app.auth_service.schemas.base import BaseResponseSchema

from typing import Optional,List
from xmlrpc.client import boolean
from pydantic import BaseModel, Field,validator


class BaseResponseModel(BaseModel):
    error : bool = False
    message: str = ""

class UserBase(BaseModel):
    userId :str=""
    email: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    countryCode: Optional[str] = None
    profileImage: Optional[str] = ""
    mobileNumber: Optional[str] = ""
    isactive: Optional[bool] = True
    
    model_config = ConfigDict(from_attributes=True)

class Users(UserBase):
    pass
class UserCreate(UserBase):
    email: EmailStr
    password: str

class UserListResponse(BaseResponseModel):
    users: List[Users]



class User(BaseModel):
	userId:str
	
	isActive:boolean= True
	username: str
	email: Optional[str] = Field(
		None, title="Enter a valid email",max_length=50
	)
	firstName: Optional[str]=""
	lastName: Optional[str]=""
	countryCode: Optional[str]=""
	profileImage: Optional[str]=""
	mobileNumber: Optional[str]=""
	password: str=""
	accountId: str=""
	is_Active:boolean= True
	doj: Optional[str]=""
	dob: Optional[str]=""
	state: Optional[str]=""
	organisation: Optional[str]=""
	designation: Optional[str]=""
	about : Optional[str]=""
	appVersion : Optional[str]=""
	creditPoints:Optional[int]=0
	subscriptionTypeId:Optional[int]=1
	
	model_config = ConfigDict(from_attributes=True)

class Current_user(User):
	accountId:str=""
	containerName:Optional[str]=""
	profileImage:Optional[str]=""

class UserDetails(User):
	pass

class SignupResponse(BaseModel):
	username: str=""
	email: str=""
	firstName: Optional[str]=""
	lastName: Optional[str]=""
	countryCode: Optional[str]=""
	isActive:boolean= True
	model_config = ConfigDict(from_attributes=True)

class ResetPasswordRequest(BaseModel):
	password: str =""
	confirmPassword: str =""

class InviteMember(BaseModel):
	firstName:str=""
	lastName:str=""
	email:str=""
	
class InviteRequest(BaseModel):
	users:List[InviteMember]

class Country(BaseModel):
	countryCode: str
	countryName: str
	model_config = ConfigDict(from_attributes=True)

class CountryDbResponse(BaseResponseModel,BaseModel):
	country: List[Country] =[]

class CountryListResponse(BaseResponseModel,BaseModel):
	country: List[Country]
	model_config = ConfigDict(from_attributes=True)

class CheckUserResponse(BaseResponseModel,BaseModel):
	user_exist: bool = False
	error: bool = False
	message: str = ""
	model_config = ConfigDict(from_attributes=True)

class AddUserRequest(BaseModel):
	username: str
	email: Optional[str] = Field(
		None, title="Enter a valid email",max_length=50
	)
	firstName: Optional[str]=""
	lastName: Optional[str]=""
	countryCode: Optional[str]=""
	profileImage: Optional[str]=""
	mobileNumber: Optional[str]=""
	isActive:boolean= False



