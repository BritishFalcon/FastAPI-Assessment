import uuid
from datetime import datetime

from fastapi_users import schemas
from pydantic import BaseModel


class UserRead(schemas.BaseUser[uuid.UUID]):
    credits: int


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


class UsageRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    credit_change: int
    note: str = None
    timestamp: datetime

    class Config:
        orm_mode = True


