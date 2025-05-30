import os
from datetime import datetime, timedelta, UTC
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import get_database_session
from models import UserModel
from dotenv import load_dotenv

load_dotenv()

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

JWT_SECRET = os.getenv("JWT_SECRET", "hello-jwt")
REFRESH_SECRET = os.getenv("REFRESH_SECRET", "hello-token")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_DURATION = timedelta(minutes=45)
REFRESH_TOKEN_DURATION = timedelta(days=14)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def generate_access_token(data: dict):
    payload = data.copy()
    expire = datetime.now(UTC) + ACCESS_TOKEN_DURATION
    payload.update({"exp": expire})
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def generate_refresh_token(data: dict):
    payload = data.copy()
    expire = datetime.now(UTC) + REFRESH_TOKEN_DURATION
    payload.update({"exp": expire})
    return jwt.encode(payload, REFRESH_SECRET, algorithm=JWT_ALGORITHM)


def create_auth_exception(status_code: int, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"message": message, "code": status_code},
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_authenticated_user(token: str = Depends(oauth2_bearer), db: Session = Depends(get_database_session)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")

        if not username or datetime.now(UTC) > datetime.fromtimestamp(payload.get("exp", 0), UTC):
            raise create_auth_exception(status.HTTP_401_UNAUTHORIZED, "Token is invalid or expired")

        user = db.query(UserModel).filter(UserModel.username == username).first()
        if not user or not user.is_active:
            raise create_auth_exception(status.HTTP_404_NOT_FOUND, "User account not found or inactive")

        return user
    except JWTError:
        raise create_auth_exception(status.HTTP_401_UNAUTHORIZED, "Authentication credentials are invalid")
