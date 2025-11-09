from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import SessionLocal
from app.schemas.user_game import *
from app.services import user_game as service
from app.core.logger_config import get_logger

router = APIRouter(prefix="/users/{user_id}/games", tags=["user_games"])
logger = get_logger(__name__)

# Helpers --------------------------------------------------------------------

async def get_db():
    async with SessionLocal() as session:
        yield session


# ENDPOINTS ------------------------------------------------------------------

# Obtener UserGame por user_id y game_id
@router.get("/{game_id}", response_model=UserGameOut)
async def get_game(user_id: int, game_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Solicitud GET /users/{user_id}/games/{game_id}")
    try:
        game = await service.get_user_game(db, user_id, game_id)
        if not game:
            logger.warning(f"Juego no encontrado (user_id={user_id}, game_id={game_id})")
            raise HTTPException(status_code=404, detail="Juego no encontrado")
        logger.info(f"Juego encontrado correctamente (user_id={user_id}, game_id={game_id})")
        return game
    except Exception as e:
        logger.exception(f"Error al obtener juego (user_id={user_id}, game_id={game_id}): {e}")
        raise HTTPException(status_code=500, detail="Error interno al obtener juego")


# Listar UserGames de un usuario
@router.get("/", response_model=List[UserGameOut])
async def list_games(user_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Solicitud GET /users/{user_id}/games (listar juegos)")
    try:
        games = await service.get_user_games(db, user_id)
        logger.info(f"Se encontraron {len(games)} juegos para el usuario {user_id}")
        return games
    except Exception as e:
        logger.exception(f"Error al listar juegos del usuario {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno al listar juegos")


# Añadir un UserGame
@router.post("/", response_model=UserGameOut, status_code=201)
async def add_game(user_id: int, data: UserGameCreate, db: AsyncSession = Depends(get_db)):
    logger.info(f"Solicitud POST /users/{user_id}/games con data={data.dict()}")
    try:
        new_game = await service.create_user_game(db, user_id, data)
        logger.info(f"Juego añadido correctamente (user_id={user_id}, game_id={new_game.game_id})")
        return new_game
    except Exception as e:
        logger.exception(f"Error al añadir juego (user_id={user_id}): {e}")
        raise HTTPException(status_code=500, detail="Error interno al añadir juego")


# Modificar un UserGame
@router.put("/{game_id}", response_model=UserGameOut)
async def update_game(user_id: int, game_id: int, data: UserGameUpdate, db: AsyncSession = Depends(get_db)):
    logger.info(f"Solicitud PUT /users/{user_id}/games/{game_id} con data={data.dict()}")
    try:
        updated = await service.update_user_game(db, user_id, game_id, data)
        if not updated:
            logger.warning(f"No se pudo actualizar: juego no encontrado (user_id={user_id}, game_id={game_id})")
            raise HTTPException(status_code=404, detail="Juego no encontrado")
        logger.info(f"Juego actualizado correctamente (user_id={user_id}, game_id={game_id})")
        return updated
    except Exception as e:
        logger.exception(f"Error al actualizar juego (user_id={user_id}, game_id={game_id}): {e}")
        raise HTTPException(status_code=500, detail="Error interno al actualizar juego")


# Eliminar un UserGame
@router.delete("/{game_id}", status_code=204)
async def delete_game(user_id: int, game_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Solicitud DELETE /users/{user_id}/games/{game_id}")
    try:
        deleted = await service.delete_user_game(db, user_id, game_id)
        if not deleted:
            logger.warning(f"No se pudo eliminar: juego no encontrado (user_id={user_id}, game_id={game_id})")
            raise HTTPException(status_code=404, detail="Juego no encontrado")
        logger.info(f"Juego eliminado correctamente (user_id={user_id}, game_id={game_id})")
        return None
    except Exception as e:
        logger.exception(f"Error al eliminar juego (user_id={user_id}, game_id={game_id}): {e}")
        raise HTTPException(status_code=500, detail="Error interno al eliminar juego")
