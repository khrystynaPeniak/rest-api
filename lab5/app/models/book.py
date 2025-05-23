from pydantic import BaseModel, Field
from typing import List
from pydantic_mongo import ObjectIdField
from datetime import datetime

class BookModel(BaseModel):
    title: str  = Field(..., min_length=1, max_length=150)
    author: str = Field(..., min_length=2, max_length=150)
    year: int = Field(..., ge=1700, le=datetime.now().year)

class BookInDB(BookModel):
    id: ObjectIdField = Field(alias="_id")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectIdField: str,
        }

class BookList(BaseModel):
    books: List[BookInDB]
