"""Password hashing and JWT issuance/verification.

Kept separate from app/api/deps.py so it has no FastAPI/HTTP knowledge and can
be unit tested (or reused by a CLI/worker) on its own.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import AuthenticationError

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return str(_pwd_context.hash(password))


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bool(_pwd_context.verify(plain_password, password_hash))


def create_access_token(user_id: UUID) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return str(jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM))


def decode_access_token(token: str) -> UUID:
    """Returns the authenticated user id, or raises AuthenticationError."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise AuthenticationError("Invalid or expired token") from exc

    subject = payload.get("sub")
    if subject is None:
        raise AuthenticationError("Invalid token payload")
    try:
        return UUID(subject)
    except ValueError as exc:
        raise AuthenticationError("Invalid token payload") from exc
