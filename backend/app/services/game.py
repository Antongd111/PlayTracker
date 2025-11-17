import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone, date

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.game import Game


# ============================================================================
# CONFIG
# ============================================================================

RAWG_API_BASE_URL = "https://api.rawg.io/api"
CACHE_TTL = timedelta(days=30)


# ============================================================================
# Helpers RAWG
# ============================================================================

async def _rawg_get(path: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
   merged = {"key": settings.RAWG_API_KEY}
   if params:
      merged.update(params)

   async with httpx.AsyncClient(timeout=20) as client:
      return await client.get(f"{RAWG_API_BASE_URL}{path}", params=merged)


def _utcnow() -> datetime:
   return datetime.now(timezone.utc)


def _to_date(s: Optional[str]) -> Optional[date]:
   if not s:
      return None
   try:
      return date.fromisoformat(s[:10])
   except ValueError:
      return None


# ============================================================================
# MAPEADORES
# ============================================================================

def format_game(game: Dict[str, Any]) -> Dict[str, Any]:
   return {
      "id": game["id"],
      "title": game["name"],
      "year": int(game["released"][:4]) if game.get("released") else 0,
      "imageUrl": game.get("background_image", ""),
      "rating": game.get("rating", 0),
   }


def format_game_detail(game: Dict[str, Any], screenshots, trailers, similar_games) -> Dict[str, Any]:
   return {
      "id": game["id"],
      "title": game["name"],
      "description": game.get("description_raw", ""),
      "releaseDate": game.get("released"),
      "imageUrl": game.get("background_image", ""),
      "rating": game.get("rating", 0),
      "platforms": [p["platform"]["name"] for p in game.get("platforms", [])],
      "genres": [g["name"] for g in game.get("genres", [])],
      "developers": [d["name"] for d in game.get("developers", [])],
      "publishers": [p["name"] for p in game.get("publishers", [])],
      "tags": [t["name"] for t in game.get("tags", [])],
      "esrbRating": game["esrb_rating"]["name"] if game.get("esrb_rating") else None,
      "metacriticScore": game.get("metacritic"),
      "metacriticUrl": game.get("metacritic_url"),
      "website": game.get("website"),
      "screenshots": [s["image"] for s in screenshots.get("results", [])],
      "videos": [
         v["data"]["480"]
         for v in trailers.get("results", [])
         if "data" in v and "480" in v["data"]
      ],
      "similarGames": [
         {"id": g["id"], "title": g["name"], "imageUrl": g.get("background_image", "")}
         for g in similar_games.get("results", [])
      ],
   }


# ============================================================================
# RAWG FETCHERS
# ============================================================================

async def fetch_game_detail_from_rawg(game_id: int) -> Dict[str, Any]:
   resp_game = await _rawg_get(f"/games/{game_id}")
   if resp_game.status_code != 200:
      raise HTTPException(status_code=500, detail="No se pudo obtener detalle del juego")

   game = resp_game.json()

   screenshots = (await _rawg_get(f"/games/{game_id}/screenshots")).json()
   trailers = (await _rawg_get(f"/games/{game_id}/movies")).json()
   similar_games = (await _rawg_get(f"/games/{game_id}/suggested")).json()

   return format_game_detail(game, screenshots, trailers, similar_games)


async def search_games(query: str) -> List[Dict[str, Any]]:
   params = {"search": query, "page_size": 10}
   response = await _rawg_get("/games", params=params)

   if response.status_code != 200:
      raise HTTPException(status_code=500, detail="Error al conectar con RAWG")

   return [format_game(g) for g in response.json().get("results", [])]


async def get_popular_games(page: int = 1, size: int = 10):
   params = {
      "ordering": "-added",
      "dates": "2025-01-01,2025-12-31",
      "page_size": size,
      "page": page,
   }

   response = await _rawg_get("/games", params=params)
   if response.status_code != 200:
      raise HTTPException(status_code=500, detail="Error al obtener juegos populares")

   return [format_game(g) for g in response.json().get("results", [])]


async def get_genres() -> Dict[str, Any]:
   response = await _rawg_get("/genres")
   if response.status_code != 200:
      raise HTTPException(status_code=500, detail="Error al obtener géneros")
   return response.json()


# ============================================================================
# BD / CACHE HELPERS
# ============================================================================

async def _get_by_rawg_id(db: AsyncSession, rawg_id: int) -> Optional[Game]:
   res = await db.execute(select(Game).where(Game.rawg_id == rawg_id))
   return res.scalar_one_or_none()


def _map_to_db(payload: Dict[str, Any]) -> Dict[str, Any]:
   def _lst(v):
      return v if isinstance(v, list) else []

   rating = None
   if payload.get("rating") is not None:
      try:
         rating = float(payload["rating"])
      except Exception:
         rating = None

   return {
      "rawg_id": payload.get("id"),
      "title": payload.get("title") or "",
      "description": payload.get("description"),
      "release_date": _to_date(payload.get("releaseDate")),
      "image_url": payload.get("imageUrl"),
      "rating": rating,
      "platforms": _lst(payload.get("platforms")),
      "genres": _lst(payload.get("genres")),
      "developers": _lst(payload.get("developers")),
      "publishers": _lst(payload.get("publishers")),
      "tags": _lst(payload.get("tags")),
      "screenshots": _lst(payload.get("screenshots")),
      "videos": _lst(payload.get("videos")),
      "similar_games": _lst(payload.get("similarGames")),
      "esrb_rating": payload.get("esrbRating"),
      "metacritic_score": payload.get("metacriticScore"),
      "metacritic_url": payload.get("metacriticUrl"),
      "website": payload.get("website"),
   }


async def _upsert_game(db: AsyncSession, payload: Dict[str, Any]) -> Game:
   data = _map_to_db(payload)
   g = await _get_by_rawg_id(db, data["rawg_id"])

   if g is None:
      g = Game(**data)
      g.fetched_at = _utcnow()
      db.add(g)
   else:
      for k, v in data.items():
         setattr(g, k, v)
      g.fetched_at = _utcnow()

   await db.flush()
   return g


# ============================================================================
# PUBLIC: OBTENER JUEGO CON CACHE
# ============================================================================

async def get_game(db: AsyncSession, rawg_id: int) -> Game:
   g = await _get_by_rawg_id(db, rawg_id)

   if g and g.fetched_at and g.fetched_at > _utcnow() - CACHE_TTL:
      return g

   payload = await fetch_game_detail_from_rawg(rawg_id)
   return await _upsert_game(db, payload)
