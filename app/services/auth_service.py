import base64
import hashlib
import hmac
import json
import time
from typing import Optional
import bcrypt
from fastapi import Request, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.config import SECRET_KEY, SESSION_COOKIE_NAME, SESSION_EXPIRE_HOURS
from app.database import get_db
from app.models.user import User


def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_session_token(user_id: int) -> str:
    """Creates a cryptographically signed, timestamped session token."""
    payload = {
        "uid": user_id,
        "exp": int(time.time()) + (SESSION_EXPIRE_HOURS * 3600),
        "iat": int(time.time()),
    }
    raw_payload = json.dumps(payload, separators=(",", ":"))
    b64_payload = base64.urlsafe_b64encode(raw_payload.encode("utf-8")).decode("utf-8").rstrip("=")
    sig = hmac.new(SECRET_KEY.encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{b64_payload}.{sig}"


def verify_session_token(token: str) -> Optional[int]:
    """Verifies a signed session token and returns the user_id if valid."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        b64_payload, signature = parts
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        # Add padding back if necessary
        padding = "=" * ((4 - len(b64_payload) % 4) % 4)
        raw_payload = base64.urlsafe_b64decode(b64_payload + padding).decode("utf-8")
        data = json.loads(raw_payload)
        if time.time() > data.get("exp", 0):
            return None
        return data.get("uid")
    except Exception:
        return None


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Returns the authenticated user or None if unauthenticated."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
    if not token:
        return None
    user_id = verify_session_token(token)
    if not user_id:
        return None
    return db.query(User).filter(User.user_id == user_id).first()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency that enforces authentication. Raises 401 if missing/invalid."""
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access this resource",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Validates user credentials."""
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def register_user(db: Session, email: str, full_name: str, password: str) -> User:
    """Registers a new user with hashed password."""
    clean_email = email.strip().lower()
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists",
        )
    user = User(
        email=clean_email,
        full_name=full_name.strip(),
        password_hash=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
