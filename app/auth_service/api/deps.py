import time
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.auth_service.schemas import User, TokenRequest
from app.auth_service.services import AUTH_SERVICE
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
        user = AUTH_SERVICE.get_user(db, id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) ->User:
    if current_user.is_active != True:
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
