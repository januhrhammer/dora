"""
Authentication module for the medicine tracker.

Provides simple authentication with a single user (no signup).
Uses JWT tokens for session management.
"""

from datetime import datetime, timedelta
from typing import Optional
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

# Security scheme
security = HTTPBearer()


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    """Login request with username and password."""
    username: str
    password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.

    Args:
        plain_password (str): The plain text password.
        hashed_password (str): The hashed password.

    Returns:
        bool: True if password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.

    Args:
        password (str): Plain text password.

    Returns:
        str: Hashed password.
    """
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticate a user against environment variables.

    The valid username and password hash are stored in:
    - AUTH_USERNAME
    - AUTH_PASSWORD_HASH

    Args:
        username (str): Username to authenticate.
        password (str): Password to verify.

    Returns:
        bool: True if authentication successful, False otherwise.
    """
    valid_username = os.getenv("AUTH_USERNAME", "admin")
    valid_password_hash = os.getenv("AUTH_PASSWORD_HASH", "")

    if username != valid_username:
        return False

    if not valid_password_hash:
        # If no hash is set, reject login for security
        return False

    return verify_password(password, valid_password_hash)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data (dict): Data to encode in the token.
        expires_delta (timedelta, optional): Token expiration time.

    Returns:
        str: Encoded JWT token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Dependency to get the current authenticated user from JWT token.

    Args:
        credentials (HTTPAuthorizationCredentials): Bearer token from request.

    Returns:
        str: Username of authenticated user.

    Raises:
        HTTPException: 401 if token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return username
