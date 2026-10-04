from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.database.models.user import User
from app.database.session import get_db
from app.users.security import decode_access_token
from app.users.service import get_user_by_id

security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Dependency verifying JWT bearer token and returning authenticated User entity."""
    if not credentials or not credentials.credentials:
        raise AuthenticationError("Authentication token is missing.")

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Malformed token: missing subject claim.")

    user = await get_user_by_id(session, user_id)
    if not user:
        raise AuthenticationError("User associated with this token no longer exists.")

    if not user.is_active:
        raise AuthenticationError("User account is inactive.")

    return user
