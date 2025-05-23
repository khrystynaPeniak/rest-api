from datetime import datetime, timedelta, UTC
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from ..database import db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/api/auth/login")

SECRET_KEY = "fastapi"
REFRESH_SECRET_KEY = "refresh-fastapi"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = timedelta(minutes=10)
REFRESH_TOKEN_EXPIRE_DAYS = timedelta(days=2)


def create_access_token(data: dict):
    token_data = data.copy()
    expire_time = datetime.now(UTC) + ACCESS_TOKEN_EXPIRE_MINUTES
    token_data.update({"exp": expire_time})
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict):
    token_data = data.copy()
    expire_time = datetime.now(UTC) + REFRESH_TOKEN_EXPIRE_DAYS
    token_data.update({"exp": expire_time})
    return jwt.encode(token_data, REFRESH_SECRET_KEY, algorithm=ALGORITHM)


def create_http_exception(status_code: int, detail: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"error": detail, "status_code": status_code},
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username or datetime.now(UTC) > datetime.fromtimestamp(payload.get("exp", 0), UTC):
            raise create_http_exception(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

        user = await db.users.find_one({"username": username})
        if not user:
            raise create_http_exception(status.HTTP_404_NOT_FOUND, "User not found")

        return user
    except JWTError:
        raise create_http_exception(status.HTTP_401_UNAUTHORIZED, "Could not validate credentials")


def verify_refresh_token(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username or datetime.now(UTC) > datetime.fromtimestamp(payload.get("exp", 0), UTC):
            raise create_http_exception(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")
        return username
    except JWTError:
        raise create_http_exception(status.HTTP_401_UNAUTHORIZED, "Could not validate refresh token")
