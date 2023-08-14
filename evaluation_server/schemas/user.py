from typing import Optional

from pydantic import BaseModel, Field


# Shared fields
class UserBase(BaseModel):
    is_superuser: bool = Field(..., title="Is Superuser")
    is_trusted: Optional[bool] = Field(True, title="Is Trusted")
    aicrowd_username: Optional[str] = Field(
        "", title="AIcrowd username", description="AIcrowd username linked to the user"
    )


# Fields to receive while User creation
class UserCreate(UserBase):
    pass


# Fields to receive while User update
class UserUpdate(UserBase):
    is_superuser: Optional[bool]


# Fields to respond
class User(UserBase):
    id: str
    api_key: str

    class Config:
        orm_mode = True
