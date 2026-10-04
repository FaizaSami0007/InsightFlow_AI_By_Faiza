from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError
from app.database.models.user import User
from app.users.schemas import UserCreate
from app.users.security import hash_password, verify_password


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Retrieve user entity by unique email."""
    result = await session.execute(select(User).where(User.email == email.strip().lower()))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: str) -> User | None:
    """Retrieve user entity by primary key ID."""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, user_in: UserCreate) -> User:
    """Register a new user after verifying email uniqueness."""
    existing = await get_user_by_email(session, user_in.email)
    if existing:
        raise ConflictError(
            message="An account with this email address already exists.",
            details={"email": user_in.email},
        )

    user = User(
        email=user_in.email,
        password_hash=hash_password(user_in.password),
        full_name=user_in.full_name.strip(),
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User:
    """Validate user credentials and active status."""
    user = await get_user_by_email(session, email)
    if not user:
        raise AuthenticationError("Invalid email or password.")

    if not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid email or password.")

    if not user.is_active:
        raise AuthenticationError("User account has been deactivated.")

    return user
