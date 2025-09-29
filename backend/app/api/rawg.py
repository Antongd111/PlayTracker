from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session

from app.core.rawg import search_games, get_game_details, get_popular_games, get_genres
from app.schemas.game import GameDetailResponse

from app.core.dependencies import get_db
from app.crud.game_catalog import upsert_game_catalog

router = APIRouter()

@router.get("/games/search")
async def search(query: str = Query(..., min_length=1)):
    return await search_games(query)

@router.get("/games/popular")
async def popular_games(page: int = 1):
    return await get_popular_games(page)

@router.get("/games/genres")
async def genres():
    return await get_genres()

@router.get("/games/{game_id}", response_model=GameDetailResponse)
async def get_game(game_id: int):
    return await get_game_details(game_id)
