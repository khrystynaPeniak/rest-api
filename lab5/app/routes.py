from fastapi import APIRouter, HTTPException
from http import HTTPStatus
from .database import db
from .models import BookModel, BookInDB, BookList
from pydantic_mongo import PydanticObjectId

router = APIRouter()

@router.post("/books/", response_model=BookInDB, status_code=HTTPStatus.CREATED)
async def create_book(book: BookModel):
    result = await db.books.insert_one(book.model_dump())
    created_book = await db.books.find_one({"_id": result.inserted_id})
    return created_book

@router.get("/books/", response_model=BookList)
async def get_books():
    books = await db.books.find().to_list(length=100)
    return {"books": books}

@router.get("/books/{book_id}", response_model=BookInDB)
async def get_book(book_id: str):
    book = await db.books.find_one({"_id": PydanticObjectId(book_id)})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.delete("/books/{book_id}", status_code=HTTPStatus.NO_CONTENT)
async def delete_book(book_id: str):
    result = await db.books.delete_one({"_id": PydanticObjectId(book_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    return None