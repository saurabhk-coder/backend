from typing import Any, Optional
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str=""
    token_type: str="bearer"
    role: Optional[str] = None
    role_id: Optional[str] = None
    permissions_json: Optional[Any] = None
    permission_json: Optional[Any] = None


class TokenRequest(BaseModel):
    sub: Optional[int] = None
