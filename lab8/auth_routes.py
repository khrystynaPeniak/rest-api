from fastapi import APIRouter, Depends, status, Request, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from pydantic import BaseModel

from auth_service import (
    REFRESH_SECRET,
    JWT_ALGORITHM,
    generate_access_token,
    generate_refresh_token,
    create_auth_exception,
    hash_password,
    verify_password,
    ACCESS_TOKEN_DURATION
)
from database import get_database_session
from models import UserModel
from schemas import UserProfileSchema, AuthTokenSchema, UserRegistrationSchema
from rate_limiter import check_request_limit

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@auth_router.post("/register", response_model=UserProfileSchema)
async def create_user_account(
        request: Request,
        user_data: UserRegistrationSchema,
        db: Session = Depends(get_database_session)
):
    await check_request_limit(request)

    if db.query(UserModel).filter(UserModel.username == user_data.username).first():
        raise create_auth_exception(status.HTTP_400_BAD_REQUEST, "Username is already taken")

    if db.query(UserModel).filter(UserModel.email == user_data.email).first():
        raise create_auth_exception(status.HTTP_400_BAD_REQUEST, "Email address is already registered")

    new_user = UserModel(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@auth_router.post("/login", response_model=AuthTokenSchema)
async def authenticate_user(
        request: Request,
        credentials: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_database_session)
):
    await check_request_limit(request)

    user = db.query(UserModel).filter(UserModel.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise create_auth_exception(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")

    if not user.is_active:
        raise create_auth_exception(status.HTTP_403_FORBIDDEN, "Account is deactivated")

    return {
        "access_token": generate_access_token({"sub": user.username}),
        "refresh_token": generate_refresh_token({"sub": user.username}),
        "token_type": "bearer",
        "expires_in": int(ACCESS_TOKEN_DURATION.total_seconds())
    }


@auth_router.post("/refresh", response_model=AuthTokenSchema)
async def renew_access_token(
        request: Request,
        token_data: RefreshTokenRequest,
        db: Session = Depends(get_database_session)
):
    await check_request_limit(request)

    try:
        payload = jwt.decode(token_data.refresh_token, REFRESH_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise create_auth_exception(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    except JWTError:
        raise create_auth_exception(status.HTTP_401_UNAUTHORIZED, "Refresh token is expired or invalid")

    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user or not user.is_active:
        raise create_auth_exception(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")

    return {
        "access_token": generate_access_token({"sub": username}),
        "refresh_token": generate_refresh_token({"sub": username}),
        "token_type": "bearer",
        "expires_in": int(ACCESS_TOKEN_DURATION.total_seconds())
    }
