from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from app.core.security import decode_access_token
from app.models.enums import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user_payload(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return payload


def require_roles(*allowed_roles: UserRole):
    """
    Usage: @router.post(..., dependencies=[Depends(require_roles(UserRole.ADMIN))])
    Keeps role checks declarative at the route level instead of scattered
    if-checks inside handlers.
    """
    async def checker(payload: dict = Depends(get_current_user_payload)) -> dict:
        if payload.get("role") not in [r.value for r in allowed_roles]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return payload
    return checker
