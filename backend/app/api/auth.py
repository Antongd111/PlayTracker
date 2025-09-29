from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import UserRegister, UserLogin
from app.core.database import get_async_session
from app.models.user import User
from sqlalchemy import select
from app.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter()

# Nuevo usuario
@router.post("/register", status_code=201)
async def register(user: UserRegister, db: AsyncSession = Depends(get_async_session)):
    
    # Comprobar si el usuario ya existe
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar():
        raise HTTPException(status_code=400, detail="El email ya está en uso")

    # Comprobar si el nombre de usuario ya existe
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalar():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")

    # Si todo va bien, creación del usuario
    new_user = User(
        email=user.email,
        username=user.username,
        hashed_password=get_password_hash(user.password)
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Se devuelve el id del usuario como respuesta
    return {"message": "Usuario registrado con éxito", "id": new_user.id}

# Inicio de sesión
@router.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(User).where(User.email == user.email))
    db_user = result.scalar_one_or_none()

    # Si no existe el usuario o la contraseña es incorrecta
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    # Se crea el token y se devuelve
    token = create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": token, "token_type": "bearer"}