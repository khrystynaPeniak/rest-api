from fastapi import APIRouter, HTTPException, Depends
from fastapi import APIRouter, HTTPException, Depends
from http import HTTPStatus
from ..database import db
from ..models.book import BookModel, BookInDB, BookList
from pydantic_mongo import PydanticObjectId
from ..utils.auth import get_current_user

router = APIRouter()


@router.post("/books/", response_model=BookInDB, status_code=HTTPStatus.CREATED)
async def create_book(book: BookModel, current_user=Depends(get_current_user)):
    book_data = book.model_dump()
    result = await db.books.insert_one(book_data)
    book_data["_id"] = result.inserted_id
    return BookInDB(**book_data)


@router.get("/books/", response_model=BookList)
async def get_books(current_user=Depends(get_current_user)):
    books = await db.books.find().to_list(length=100)
    return {"books": books}


@router.get("/books/{book_id}", response_model=BookInDB)
async def get_book(book_id: str, current_user=Depends(get_current_user)):
    try:
        book = await db.books.find_one({"_id": PydanticObjectId(book_id)})
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        return book
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid book ID format")


@router.delete("/books/{book_id}", status_code=HTTPStatus.NO_CONTENT)
async def delete_book(book_id: str, current_user=Depends(get_current_user)):
    try:
        result = await db.books.delete_one({"_id": PydanticObjectId(book_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Book not found")
        return None
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid book ID format")


@router.put("/books/{book_id}", response_model=BookInDB)
async def update_book(book_id: str, book: BookModel, current_user=Depends(get_current_user)):
    try:
        result = await db.books.update_one(
            {"_id": PydanticObjectId(book_id)},
            {"$set": book.model_dump()}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Book not found")

        updated_book = await db.books.find_one({"_id": PydanticObjectId(book_id)})
        return updated_book
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid book ID format")
