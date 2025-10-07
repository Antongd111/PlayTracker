from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rawg import search_games, get_game_details, get_popular_games, get_genres
from app.schemas.game import GameDetailResponse, SimilarGame

from app.core.dependencies import get_db
from app.services.game_cache import get_or_fetch_game

router = APIRouter()


def _to_response(game) -> GameDetailResponse:
    # Coalesce: nunca None en campos no opcionales del schema
    return GameDetailResponse(
        id=game.rawg_id,
        title=game.title or "",
        description=game.description or "",
        releaseDate=game.release_date.isoformat() if game.release_date else None,
        imageUrl=game.image_url or "",
        rating=float(game.rating) if game.rating is not None else 0.0,
        platforms=game.platforms or [],
        genres=game.genres or [],
        developers=game.developers or [],
        publishers=game.publishers or [],
        tags=game.tags or [],
        esrbRating=game.esrb_rating,
        metacriticScore=game.metacritic_score,
        metacriticUrl=game.metacritic_url,
        website=game.website,
        screenshots=game.screenshots or [],
        videos=game.videos or [],
        similarGames=[],
    )


# ENDPOINTS ------------------------------------------------------------------

# Obtener juegos por búsqueda
@router.get("/games/search")
async def search(query: str = Query(..., min_length=1)):
    return await search_games(query)

# Obtener juegos populares
@router.get("/games/popular")
async def popular_games(page: int = 1):
    return await get_popular_games(page)

# Obtener géneros
@router.get("/games/genres")
async def genres():
    return await get_genres()

# Obtener detalles de un juego (y guardarlo en el catálogo si no existe)
@router.get("/games/{game_id}", response_model=GameDetailResponse)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    try:
        g = await get_or_fetch_game(db, game_id)
        await db.commit()
    except Exception as e:
        # Si quieres ver claramente si es error de DB/serialización,
        # cambia este 502 por 500 para distingir de errores de red con RAWG
        raise HTTPException(status_code=500, detail=f"Cache/DB error: {e}")
    if not g:
        raise HTTPException(status_code=404, detail="Game not found")
    return _to_response(g)