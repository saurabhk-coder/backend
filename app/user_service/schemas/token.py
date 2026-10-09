from typing import Optional
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str=""
    token_type: str="bearer"
    role: Optional[str] = None
    role_id: Optional[str] = None


class TokenRequest(BaseModel):
    sub: Optional[int] = None
