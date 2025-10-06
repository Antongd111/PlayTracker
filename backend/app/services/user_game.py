from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user_game import UserGame
from app.schemas.user_game import UserGameCreate, UserGameUpdate
from app.core.config import settings

import os
import httpx
from typing import Optional

RAWG_API_KEY = settings.RAWG_API_KEY


async def _fetch_rawg_preview(rawg_id: int) -> Optional[dict]:
    """
    Devuelve un dict con datos mínimos de un juego desde RAWG,
    o None si falla o no hay API_KEY.
    """
    if not RAWG_API_KEY:
        return None
    url = f"https://api.rawg.io/api/games/{rawg_id}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, params={"key": RAWG_API_KEY})
            r.raise_for_status()
            data = r.json()

        title = data.get("name") or ""
        img = data.get("background_image")
        rel = data.get("released")  # "YYYY-MM-DD"
        year = int(rel.split("-")[0]) if rel else None
        return {"game_title": title, "image_url": img, "release_year": year}
    except Exception:
        return None


async def get_user_games(db: AsyncSession, user_id: int):
    result = await db.execute(select(UserGame).where(UserGame.user_id == user_id))
    return result.scalars().all()


async def get_user_game(db: AsyncSession, user_id: int, game_id: int):
    result = await db.execute(
        select(UserGame).where(UserGame.user_id == user_id, UserGame.game_rawg_id == game_id)
    )
    return result.scalar_one_or_none()


async def create_user_game(db: AsyncSession, user_id: int, data: UserGameCreate):
    payload = data.dict(exclude_unset=True)

    # si faltan datos de preview, intentamos completarlos
    if not all(payload.get(k) for k in ("game_title", "image_url", "release_year")):
        preview = await _fetch_rawg_preview(payload["game_rawg_id"])
        if preview:
            for k, v in preview.items():
                payload.setdefault(k, v)

    game = UserGame(**payload, user_id=user_id)
    db.add(game)
    await db.commit()
    await db.refresh(game)
    return game


async def update_user_game(db: AsyncSession, user_id: int, game_id: int, data: UserGameUpdate):
    game = await get_user_game(db, user_id, game_id)
    if not game:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(game, field, value)

    # si sigue faltando algún campo de preview, intenta completarlo
    if not all(getattr(game, k) for k in ("game_title", "image_url", "release_year")):
        preview = await _fetch_rawg_preview(game.game_rawg_id)
        if preview:
            if not game.game_title:
                game.game_title = preview["game_title"]
            if not game.image_url:
                game.image_url = preview["image_url"]
            if not game.release_year:
                game.release_year = preview["release_year"]

    await db.commit()
    await db.refresh(game)
    return game


async def delete_user_game(db: AsyncSession, user_id: int, game_id: int):
    game = await get_user_game(db, user_id, game_id)
    if not game:
        return None

    await db.delete(game)
    await db.commit()
    return game
