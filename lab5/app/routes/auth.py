from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from ..database import db
from ..models.user import UserModel, Token, RefreshToken
from ..utils.auth import (
    create_access_token,
    create_refresh_token,
    create_http_exception,
    verify_refresh_token
)

auth_router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def authenticate_user(username: str, password: str):
    user = await db.users.find_one({"username": username})
    if not user:
        return False
    if not verify_password(password, user["password"]):
        return False
    return user


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserModel):
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    hashed_password = get_password_hash(user.password)

    user_data = {
        "username": user.username,
        "password": hashed_password
    }

    result = await db.users.insert_one(user_data)

    return {"message": "User created successfully", "user_id": str(result.inserted_id)}


@auth_router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise create_http_exception(
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect username or password"
        )

    access_token = create_access_token(data={"sub": user["username"]})
    refresh_token = create_refresh_token(data={"sub": user["username"]})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@auth_router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_data: RefreshToken):
    username = verify_refresh_token(refresh_data.refresh_token)

    user = await db.users.find_one({"username": username})
    if not user:
        raise create_http_exception(status.HTTP_404_NOT_FOUND, "User not found")

    access_token = create_access_token(data={"sub": username})
    new_refresh_token = create_refresh_token(data={"sub": username})

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }
