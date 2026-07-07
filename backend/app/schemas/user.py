from datetime import datetime

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=7, max_length=32)


class UserRead(BaseModel):
    id: int
    name: str
    phone: str
    created_at: datetime

    model_config = {"from_attributes": True}
