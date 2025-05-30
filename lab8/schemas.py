from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class BookCreateSchema(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    author: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1700, le=datetime.now().year)

    class Config:
        from_attributes = True


class BookResponseSchema(BookCreateSchema):
    id: int
    owner_id: int

    class Config:
        from_attributes = True


class UserRegistrationSchema(BaseModel):
    username: str = Field(min_length=3, max_length=150)
    email: EmailStr
    password: str = Field(min_length=6)


class UserProfileSchema(BaseModel):
    id: int
    username: str
    email: str
    is_active: int

    class Config:
        from_attributes = True


class AuthTokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenDataSchema(BaseModel):
    username: Optional[str] = None
    exp: Optional[int] = None
