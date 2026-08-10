from typing import Optional
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str=""
    token_type: str="bearer"


class TokenRequest(BaseModel):
    sub: Optional[int] = None
