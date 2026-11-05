from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.config import SESSION_COOKIE_NAME, SESSION_EXPIRE_HOURS
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, UserResponse, TokenResponse
from app.services.auth_service import (
    authenticate_user,
    register_user,
    create_session_token,
    get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Registers a new user account."""
    user = register_user(db, payload.email, payload.name, payload.password)
    return UserResponse(
        id=user.user_id,
        email=user.email,
        name=user.full_name,
        created_at=user.created_at,
    )

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Authenticates credentials and sets a secure HttpOnly session cookie."""
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_session_token(user.user_id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_EXPIRE_HOURS * 3600,
        httponly=True,
        samesite="lax",
    )
    user_res = UserResponse(
        id=user.user_id,
        email=user.email,
        name=user.full_name,
        created_at=user.created_at,
    )
    return TokenResponse(access_token=token, token_type="bearer", user=user_res)

@router.post("/logout")
def logout(response: Response):
    """Clears the session cookie."""
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user profile."""
    return UserResponse(
        id=current_user.user_id,
        email=current_user.email,
        name=current_user.full_name,
        created_at=current_user.created_at,
    )
