from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import SessionLocal
from app.schemas.user import UserOut, UserCreate, UserUpdate
from app.services import user as service
from app.core.dependencies import get_current_user
from app.models.user import User
from app.core.logger_config import get_logger

router = APIRouter(prefix="/users", tags=["users"])
logger = get_logger(__name__)

# Helpers --------------------------------------------------------------------

async def get_db():
    async with SessionLocal() as session:
        yield session


async def get_user_or_404(user_id: int, db: AsyncSession) -> User:
    logger.info(f"Buscando usuario con ID {user_id}")
    user = await service.get_user(db, user_id)
    if not user:
        logger.warning(f"Usuario con ID {user_id} no encontrado")
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    logger.info(f"Usuario con ID {user_id} encontrado correctamente")
    return user


# ENDPOINTS ------------------------------------------------------------------

# Listado de usuarios
@router.get("/", response_model=List[UserOut])
async def read_users(db: AsyncSession = Depends(get_db), q: Optional[str] = None):
    logger.info(f"Solicitud GET /users (q={q})")
    try:
        if q:
            users = await service.search_users(db, q)
            logger.info(f"Se encontraron {len(users)} usuarios con búsqueda '{q}'")
            return users
        users = await service.get_users(db)
        logger.info(f"Se encontraron {len(users)} usuarios en total")
        return users
    except Exception as e:
        logger.exception(f"Error al listar usuarios: {e}")
        raise HTTPException(status_code=500, detail="Error interno al listar usuarios")


# Obtener el usuario asociado al token
@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    logger.info(f"Solicitud GET /users/me del usuario {current_user.id}")
    return current_user


# Obtener un usuario por Id
@router.get("/{user_id}", response_model=UserOut)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Solicitud GET /users/{user_id}")
    try:
        return await get_user_or_404(user_id, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error al obtener usuario con ID {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno al obtener usuario")


# Crear un usuario
@router.post("/", response_model=UserOut, status_code=201)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    logger.info(f"Solicitud POST /users (crear usuario con email={user.email})")
    try:
        created = await service.create_user(db, user)
        logger.info(f"Usuario creado correctamente (id={created.id}, email={created.email})")
        return created
    except Exception as e:
        logger.exception(f"Error al crear usuario ({user.email}): {e}")
        raise HTTPException(status_code=500, detail="Error interno al crear usuario")


# Modificar un usuario
@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info(f"Solicitud PATCH /users/{user_id} del usuario autenticado {current_user.id}")
    if current_user.id != user_id:
        logger.warning(f"Intento de modificación no autorizada: user {current_user.id} → target {user_id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    try:
        await get_user_or_404(user_id, db)
        updated = await service.update_user(db, user_id, user_update)
        logger.info(f"Usuario {user_id} actualizado correctamente")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error al actualizar usuario {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno al actualizar usuario")


# Borrar un usuario
@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info(f"Solicitud DELETE /users/{user_id} del usuario autenticado {current_user.id}")
    if current_user.id != user_id:
        logger.warning(f"Intento de eliminación no autorizada: user {current_user.id} → target {user_id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    try:
        await get_user_or_404(user_id, db)
        await service.delete_user(db, user_id)
        logger.info(f"Usuario {user_id} eliminado correctamente")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error al eliminar usuario {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno al eliminar usuario")
