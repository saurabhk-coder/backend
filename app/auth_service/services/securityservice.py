from datetime import datetime, timedelta, timezone
from typing import Callable, Optional
from abc import ABC, abstractmethod

from fastapi import FastAPI
from jose import jwt
from passlib.context import CryptContext

from ...core import AppSettings
from ..schemas import Token


PWD_CONTEXT = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


class ISecurityService(ABC):

    @abstractmethod
    def create_access_token(
        self,
        subject: str,
        expires_delta: Optional[timedelta] = None,
    ) -> Token:
        pass

    @abstractmethod
    def verify_password(
        self,
        plain_password: str,
        hashed_password: str,
    ) -> bool:
        pass

    @abstractmethod
    def get_password_hash(
        self,
        password: str,
    ) -> str:
        pass

    @abstractmethod
    def update_schema_name(
        self,
        app: FastAPI,
        function: Callable,
        name: str,
    ) -> None:
        pass


class SecurityService(ISecurityService):

    def create_access_token(
        self,
        subject: str,
        expires_delta: Optional[timedelta] = None,
    ) -> Token:

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = (
                datetime.now(timezone.utc)
                + timedelta(
                    minutes=AppSettings.API.ACCESS_TOKEN_EXPIRE_MINUTES
                )
            )

        to_encode = {
            "exp": expire,
            "sub": str(subject),
        }

        encoded_jwt = jwt.encode(
            to_encode,
            AppSettings.API.SECRET_KEY,
            algorithm=AppSettings.API.ALGORITHM,
        )

        return Token(
            access_token=encoded_jwt,
            token_type="bearer",
        )

    def verify_password(
        self,
        plain_password: str,
        hashed_password: str,
    ) -> bool:
        return PWD_CONTEXT.verify(
            plain_password,
            hashed_password,
        )

    def get_password_hash(
        self,
        password: str,
    ) -> str:
        return PWD_CONTEXT.hash(password)

    def update_schema_name(
        self,
        app: FastAPI,
        function: Callable,
        name: str,
    ) -> None:

        for route in app.routes:

            endpoint = getattr(route, "endpoint", None)

            if endpoint is not function:
                continue

            body_field = getattr(route, "body_field", None)

            if body_field is None:
                return

            model_type = getattr(body_field, "type_", None)

            if model_type is None:
                return

            model_type.__name__ = name
            break

    def decodeJWT(self, token: str) -> Optional[dict]:

        try:
            decoded_token = jwt.decode(
                token,
                AppSettings.API.SECRET_KEY,
                algorithms=[AppSettings.API.ALGORITHM],
            )

            return decoded_token

        except Exception:
            return None


SECURITY_SERVICE: ISecurityService = SecurityService()