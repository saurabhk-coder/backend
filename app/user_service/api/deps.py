import time
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from ..schemas import User, TokenRequest
from ..services import USER_SERVICE
from ...core import AppSettings
from app.auth_service.db.session import SessionLocal, SessionManager

reusable_oauth2 = OAuth2PasswordBearer( tokenUrl=f"{AppSettings.API.API_V1_STR}/login")

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_user(
    #db: Session = Depends(get_db), 
    token: str = Depends(reusable_oauth2)
) -> User:
    try:
        decoded_token = jwt.decode(token, AppSettings.API.SECRET_KEY, algorithms=[AppSettings.API.ALGORITHM])
        user_id = decoded_token['sub']
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    with SessionManager() as db:
        user = USER_SERVICE.get_user(db, id=user_id)
        if not user:
            users = USER_SERVICE.get_user_me(db, id=user_id)
            if not users:
                raise HTTPException(status_code=404, detail="User not found")
        else:
            response = User
            response.userId = str(user.user_id)
            response.username = user.username
            response.firstName = user.first_name
            response.lastName = user.last_name
            response.email = user.email
            response.countryCode = user.country_code
            response.isActive = user.is_active
            response.accountId = str(user.account_id)
            response.containerName = user.container_name
            response.mobileNumber = user.mobile_number
            response.doj = user.doj
            response.dob = user.dob
            response.designation = user.designation
            response.about = user.about
            response.organisation = user.organisation
            response.state = user.state
            response.profileImage = user.profile_image
            response.creditPoints = user.credit_points
            response.appVersion = user.app_version
            return response


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) ->User:
    if current_user.isActive != True:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_superuser(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user
