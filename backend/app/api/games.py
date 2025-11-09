from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.game import search_games, get_game_from_rawg, get_popular_games, get_genres
from app.schemas.game import GameDetailResponse
from app.core.dependencies import get_db
from app.services.game_cache import get_or_fetch_game
from app.core.logger_config import get_logger

# Crear router y logger del módulo
router = APIRouter()
logger = get_logger(__name__)

# ENDPOINTS ------------------------------------------------------------------

# Buscar juegos
@router.get("/games/search")
async def search(query: str = Query(..., min_length=1)):
    logger.info(f"Solicitud de búsqueda de juegos: query='{query}'")
    try:
        results = await search_games(query)
        logger.info(f"Se encontraron {len(results)} resultados para '{query}'")
        return results
    except Exception as e:
        logger.exception(f"Error durante la búsqueda de juegos: {e}")
        raise HTTPException(status_code=500, detail="Error interno al buscar juegos.")

# Obtener juegos populares
@router.get("/games/popular")
async def popular_games(page: int = 1):
    logger.info(f"Solicitud de juegos populares (página {page})")
    try:
        games = await get_popular_games(page)
        logger.info(f"Se obtuvieron {len(games)} juegos populares en la página {page}")
        return games
    except Exception as e:
        logger.exception(f"Error al obtener juegos populares: {e}")
        raise HTTPException(status_code=500, detail="Error interno al obtener juegos populares.")

# Obtener géneros
@router.get("/games/genres")
async def genres():
    logger.info("Solicitud de lista de géneros de juegos")
    try:
        genres_list = await get_genres()
        logger.info(f"Se obtuvieron {len(genres_list)} géneros.")
        return genres_list
    except Exception as e:
        logger.exception(f"Error al obtener géneros: {e}")
        raise HTTPException(status_code=500, detail="Error interno al obtener géneros.")

# Obtener detalles de un juego (y guardarlo en caché si no existe)
@router.get("/games/{game_id}", response_model=GameDetailResponse)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Solicitud de detalles del juego con ID {game_id}")
    try:
        g = await get_or_fetch_game(db, game_id)
        await db.commit()
        if not g:
            logger.warning(f"Juego con ID {game_id} no encontrado.")
            raise HTTPException(status_code=404, detail="Game not found")
        logger.info(f"Juego con ID {game_id} obtenido correctamente.")
        return g
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error al obtener detalles del juego {game_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Cache/DB error: {e}")
