from typing import Any, Dict

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.models.user import User
from app.database.session import get_db
from app.users.dependencies import get_current_user
from app.users.schemas import LoginRequest, TokenResponse, UserCreate, UserResponse
from app.users.security import create_access_token
from app.users.service import authenticate_user, create_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Register new user")
async def register(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_db),
) -> User:
    """Create a new user account with validated email and password."""
    user = await create_user(session, user_in)
    return user


@router.post("/login", response_model=TokenResponse, summary="Authenticate user and obtain JWT token")
async def login(
    login_data: LoginRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Validate user credentials and return a signed JWT bearer token."""
    user = await authenticate_user(session, login_data.email, login_data.password)
    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    expires_in = settings.access_token_expire_minutes * 60

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse, summary="Get current authenticated user profile")
async def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    """Return the profile of the currently authenticated user."""
    return current_user


@router.post("/logout", summary="Logout current session")
async def logout(
    _: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Client-side token disposal endpoint."""
    return {"status": "ok", "message": "Successfully logged out."}
