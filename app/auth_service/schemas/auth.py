from typing import List, Optional
import re

from fastapi import Response
from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseResponseModel(BaseModel):
    error: bool = False
    message: str = ""
    success: bool = True


class SignupRequest(BaseModel):
    username: Optional[str] = ""
    email: Optional[str] = Field(
        default=None,
        title="Enter a valid email",
        max_length=50,
    )
    password: Optional[str] = Field(
        default=None,
        title="Enter a valid Password",
        max_length=100,
    )
    confirmPassword: str

    firstName: str = ""
    middleName: Optional[str] = ""
    lastName: str = ""
    countryCode: Optional[str] = ""
    profileImage: Optional[str] = ""
    mobileNumber: Optional[str] = ""
    appleId: Optional[str] = ""
    accountName: Optional[str] = ""
    isActive: bool = True

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        if value is None or value == "":
            return value

        regex = r"^(\w|\.|_|-)+@(\w|_|-|\.)+\.\w{2,3}$"

        if re.search(regex, value) is None:
            raise ValueError("Provided Email is not valid email")

        return value

    @field_validator("password")
    @classmethod
    def valid_password(cls, value):
        if value is None or value == "":
            raise ValueError("Password cannot be empty!")

        return value

    @field_validator("confirmPassword")
    @classmethod
    def passwords_match(cls, value, info):
        password = info.data.get("password")

        if password is not None and value != password:
            raise ValueError(
                "Password and Confirm Password are not same!"
            )

        return value


class GoogleAuthRequest(BaseModel):
    email: Optional[str] = ""
    firstName: str = ""
    middleName: Optional[str] = ""
    lastName: Optional[str] = ""
    appleId: Optional[str] = ""
    token: str
    loginType: str
    isActive: bool = True


class SignupDBRequest(BaseModel):
    username: str
    email: str = ""
    password_salt: str = ""
    confirmPassword: str

    firstName: str = ""
    middleName: Optional[str] = ""
    lastName: str = ""
    countryCode: str = ""
    profileImage: Optional[str] = ""
    appleId: Optional[str] = ""
    mobileNumber: Optional[str] = ""
    isActive: bool = True
    accountId: str = ""


class User(BaseModel):
    username: str
    email: Optional[str] = Field(
        default=None,
        title="Enter a valid email",
        max_length=50,
    )

    firstName: Optional[str] = ""
    lastName: Optional[str] = ""
    countryCode: Optional[str] = ""
    profileImage: Optional[str] = ""
    mobileNumber: Optional[str] = ""
    password: str = ""
    accountId: str = ""
    is_Active: bool = True


class SignupResponse(BaseResponseModel):
    username: str = ""
    email: str = ""
    firstName: Optional[str] = ""
    lastName: Optional[str] = ""
    countryCode: Optional[str] = ""
    isActive: bool = True
    accountId: str = ""

    userId: Optional[str] = None
    containerName: str = ""
    profileImage: Optional[str] = None
    mobileNumber: Optional[str] = None

    creditPoints: Optional[int] = 0
    subscriptionTypeId: Optional[int] = 1

    model_config = ConfigDict(from_attributes=True)


class GoogleAuthResponse(BaseResponseModel):
    username: str = ""
    email: str = ""
    firstName: Optional[str] = ""
    lastName: Optional[str] = ""
    countryCode: Optional[str] = ""
    isActive: bool = True
    accountId: str = ""

    userId: Optional[str] = None
    containerName: str = ""
    profileImage: Optional[str] = None
    mobileNumber: Optional[str] = None

    creditPoints: Optional[int] = 0
    subscriptionTypeId: Optional[int] = 1

    token: str = ""
    loginType: str = ""

    model_config = ConfigDict(from_attributes=True)


class UpdateProfile(BaseModel):
    email: str = ""
    firstName: Optional[str] = ""
    lastName: Optional[str] = ""
    countryCode: Optional[str] = ""
    profileImage: Optional[str] = ""
    mobileNumber: Optional[str] = ""
    doj: Optional[str] = ""
    dob: Optional[str] = ""
    state: Optional[str] = ""
    organisation: Optional[str] = ""
    designation: Optional[str] = ""
    about: Optional[str] = ""


class FileUploadResponse(BaseModel):
    file_key: str
    file_name: str
    container_name: str
    file_size: str
    content_type: str
    file_url: str


class UpdateProfileResponse(BaseResponseModel):
    firstName: Optional[str] = ""
    lastName: Optional[str] = ""
    countryCode: Optional[str] = ""
    profileImage: Optional[str] = ""
    mobileNumber: Optional[str] = ""
    doj: Optional[str] = ""
    dob: Optional[str] = ""
    state: Optional[str] = ""
    organisation: Optional[str] = ""
    designation: Optional[str] = ""
    about: Optional[str] = ""

    model_config = ConfigDict(from_attributes=True)


class ResetPasswordRequest(BaseModel):
    username: str = ""
    password: str = ""
    confirmPassword: str = ""


class VersionUpdate(BaseModel):
    username: str = ""
    appVersion: str = ""


class Country(BaseModel):
    countryCode: str
    countryName: str

    model_config = ConfigDict(from_attributes=True)


class CountryDbResponse(BaseResponseModel):
    country: List[Country] = []


class CountryListResponse(BaseResponseModel):
    country: List[Country]

    model_config = ConfigDict(from_attributes=True)


class CheckUserResponse(BaseResponseModel):
    user_exist: bool = False
    error: bool = False
    message: str = ""

    model_config = ConfigDict(from_attributes=True)


class HTMLResponse(Response):
    media_type = "text/html"