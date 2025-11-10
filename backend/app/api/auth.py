from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_session
from app.schemas.auth import UserRegister, UserLogin
from app.services import auth as service
from app.core.logger_config import get_logger

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)

# Registrar nuevo usuario
@router.post("/register", status_code=201)
async def register(user: UserRegister, db: AsyncSession = Depends(get_async_session)):
    logger.info(f"Solicitud POST /auth/register para {user.email}")
    try:
        new_user = await service.register_user(db, user)
        logger.info(f"Usuario registrado correctamente (id={new_user.id})")
        return {"message": "Usuario registrado con éxito", "id": new_user.id}
    except HTTPException as e:
        logger.warning(f"Registro fallido ({user.email}): {e.detail}")
        raise
    except Exception as e:
        logger.exception(f"Error interno durante el registro de {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Error interno al registrar usuario")


# Inicio de sesión
@router.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_async_session)):
    logger.info(f"Solicitud POST /auth/login para {user.email}")
    try:
        result = await service.login_user(db, user)
        logger.info(f"Inicio de sesión completado para {user.email}")
        return result
    except HTTPException as e:
        logger.warning(f"Login fallido ({user.email}): {e.detail}")
        raise
    except Exception as e:
        logger.exception(f"Error interno durante el login de {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Error interno al iniciar sesión")
