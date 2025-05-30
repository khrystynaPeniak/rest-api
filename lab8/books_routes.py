from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from database import get_database_session
from auth_service import get_authenticated_user
from models import BookModel, UserModel
from schemas import BookResponseSchema, BookCreateSchema
from rate_limiter import check_request_limit

books_router = APIRouter(prefix="/books", tags=["Books Management"])


def find_book_by_id(book_id: int, db: Session, user: UserModel = None):
    if user:
        book = db.query(BookModel).filter(
            BookModel.id == book_id,
            BookModel.owner_id == user.id
        ).first()
        if not book:
            raise HTTPException(
                status_code=404,
                detail=f"Book with ID {book_id} not found in your collection"
            )
    else:
        book = db.query(BookModel).filter(BookModel.id == book_id).first()
        if not book:
            raise HTTPException(
                status_code=404,
                detail=f"Book with ID {book_id} not found"
            )
    return book


@books_router.get("/", response_model=List[BookResponseSchema])
async def fetch_all_books(
        request: Request,
        db: Session = Depends(get_database_session)
):
    await check_request_limit(request, user_id=None)
    books = db.query(BookModel).all()
    return books


@books_router.post("/", response_model=BookResponseSchema, status_code=201)
async def add_new_book(
        request: Request,
        book_data: BookCreateSchema,
        db: Session = Depends(get_database_session),
        current_user: UserModel = Depends(get_authenticated_user)
):
    await check_request_limit(request, user_id=current_user.id)

    new_book = BookModel(
        **book_data.model_dump(),
        owner_id=current_user.id
    )
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book


@books_router.get("/{book_id}", response_model=BookResponseSchema)
async def get_book_details(
        request: Request,
        book_id: int,
        db: Session = Depends(get_database_session)
):
    await check_request_limit(request, user_id=None)
    return find_book_by_id(book_id, db)


@books_router.put("/{book_id}", response_model=BookResponseSchema)
async def update_book_info(
        request: Request,
        book_id: int,
        updated_data: BookCreateSchema,
        db: Session = Depends(get_database_session),
        current_user: UserModel = Depends(get_authenticated_user)
):
    await check_request_limit(request, user_id=current_user.id)

    book = find_book_by_id(book_id, db, current_user)
    for field, value in updated_data.model_dump().items():
        setattr(book, field, value)

    db.commit()
    db.refresh(book)
    return book


@books_router.delete("/{book_id}", status_code=204)
async def remove_book(
        request: Request,
        book_id: int,
        db: Session = Depends(get_database_session),
        current_user: UserModel = Depends(get_authenticated_user)
):
    await check_request_limit(request, user_id=current_user.id)

    book = find_book_by_id(book_id, db, current_user)
    db.delete(book)
    db.commit()
    return None
