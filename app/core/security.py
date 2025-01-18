# app/core/security.py

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from app.core.config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token handling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


async def validate_token(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    """Validate JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)

        if datetime.fromtimestamp(token_data.exp) < datetime.utcnow():
            raise credentials_exception

        return token_data

    except JWTError:
        raise credentials_exception


# Rate limiting implementation
from fastapi import Request
import time
from typing import Dict, Tuple


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = {}

    def is_allowed(self, key: str) -> Tuple[bool, float]:
        """Check if request is allowed based on rate limiting."""
        now = time.time()
        minute_ago = now - 60

        if key not in self.requests:
            self.requests[key] = []

        # Clean old requests
        self.requests[key] = [req_time for req_time in self.requests[key]
                              if req_time > minute_ago]

        # Check if rate limit is exceeded
        if len(self.requests[key]) >= self.requests_per_minute:
            retry_after = 60 - (now - self.requests[key][0])
            return False, retry_after

        self.requests[key].append(now)
        return True, 0


# Initialize rate limiter
rate_limiter = RateLimiter()


async def check_rate_limit(request: Request):
    """Rate limiting dependency."""
    key = request.client.host
    allowed, retry_after = rate_limiter.is_allowed(key)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
            headers={"Retry-After": str(int(retry_after))}
        )


# Security middleware for CORS, XSS, etc.
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.csrf import CSRFMiddleware
from fastapi import FastAPI


def add_security_middleware(app: FastAPI) -> None:
    """Add security middleware to FastAPI application."""

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Modify in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # CSRF protection
    app.add_middleware(
        CSRFMiddleware,
        secret=settings.SECRET_KEY,
    )


# Content security utilities
import magic
import hashlib


def validate_file_type(content: bytes, allowed_types: set) -> bool:
    """Validate file type using magic numbers."""
    mime = magic.Magic(mime=True)
    file_type = mime.from_buffer(content)
    return file_type in allowed_types


def generate_file_hash(content: bytes) -> str:
    """Generate SHA-256 hash of file content."""
    return hashlib.sha256(content).hexdigest()