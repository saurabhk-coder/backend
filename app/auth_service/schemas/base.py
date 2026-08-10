import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class DateTimeModelMixin(BaseModel):
    created_at: Optional[datetime.datetime] = None

    @field_validator("created_at", mode="before")
    @classmethod
    def default_datetime(cls, value):
        return value or datetime.datetime.now()


class BaseResponseSchema(BaseModel):
    error: bool = False
    message: str = "Response Successful"
    success: bool = True

    model_config = ConfigDict(
        from_attributes=True
    )