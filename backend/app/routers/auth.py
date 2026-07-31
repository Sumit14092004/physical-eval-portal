from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import get_db
from app.models.user import User
from app.core.security import verify_password, create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    token = create_access_token(subject=str(user.id), role=user.role.value)
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role.value,
        "full_name": user.full_name,
    }
