from pydantic import BaseModel, Field
from typing import Optional
from pydantic_mongo import ObjectIdField


class UserModel(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserInDB(BaseModel):
    id: ObjectIdField = Field(alias="_id")
    username: str

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectIdField: str,
        }


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class RefreshToken(BaseModel):
    refresh_token: str
