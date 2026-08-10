from typing import Optional

from pydantic import BaseModel

from app.auth_service.schemas.auth import BaseResponseModel


class Token(BaseResponseModel):
    access_token: str = ""
    token_type: str = "bearer"


class TokenRequest(BaseModel):
    sub: Optional[int] = None