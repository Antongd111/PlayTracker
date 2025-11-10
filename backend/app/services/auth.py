# app/services/auth.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token
from app.schemas.auth import UserRegister, UserLogin

async def register_user(db: AsyncSession, user_data: UserRegister):
    # Comprobar email duplicado
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está en uso"
        )

    # Comprobar username duplicado
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está en uso"
        )

    # Crear usuario
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password)
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


async def login_user(db: AsyncSession, credentials: UserLogin):
    result = await db.execute(select(User).where(User.email == credentials.email))
    db_user = result.scalar_one_or_none()

    if not db_user or not verify_password(credentials.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email o contraseña incorrectos")

    # Crear token JWT
    token = create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": token, "token_type": "bearer"}
