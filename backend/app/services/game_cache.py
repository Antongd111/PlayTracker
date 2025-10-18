# app/services/game_cache.py
from __future__ import annotations
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta, timezone, date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.game import Game
from app.services.rawg import get_game_from_rawg

# ------------------------------------------------------------------------------
# Caché de juegos obtenidos desde RAWG
# ------------------------------------------------------------------------------
# Este servicio consulta RAWG para un juego concreto, transforma el resultado
# (ya formateado por format_game_detail -> camelCase) a nuestro modelo Game y
# lo persiste (insert/update). Aplica una política de TTL para evitar llamadas
# innecesarias a RAWG mientras el registro esté “fresco”.
# ------------------------------------------------------------------------------

CACHE_TTL = timedelta(days=30)  # Tiempo considerado "fresco" en caché (en días)


def _utcnow() -> datetime:
    """
    Devuelve la fecha y hora actual en UTC.

    Returns:
        datetime: Momento actual con zona horaria UTC.
    """
    return datetime.now(timezone.utc)


async def _get_by_rawg_id(db: AsyncSession, rawg_id: int) -> Optional[Game]:
    """
    Recupera un juego por su `rawg_id`.

    Args:
        db (AsyncSession): Sesión asíncrona de SQLAlchemy.
        rawg_id (int): Identificador del juego en RAWG.

    Returns:
        Optional[Game]: Instancia de Game si existe, o None si no se encontró.
    """
    res = await db.execute(select(Game).where(Game.rawg_id == rawg_id))
    return res.scalar_one_or_none()


def _to_date(s: Optional[str]) -> Optional[date]:
    """
    Convierte una fecha en formato ISO `YYYY-MM-DD` (o prefijo compatible) a `date`.

    Args:
        s (Optional[str]): Cadena con la fecha (p.ej. "2025-10-07").

    Returns:
        Optional[date]: Objeto date si el parseo es válido, None en caso contrario.
    """
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def _map_formatted_detail(p: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mapea el diccionario devuelto por `format_game_detail` (camelCase) a los
    campos de nuestro modelo `Game`.

    Notas:
    - Esta función **asume** que `get_game_from_rawg()` ya ha aplicado
      `format_game_detail`, es decir, que `p` viene en camelCase y con campos
      reducidos (title, imageUrl, releaseDate, etc.).
    - Se asegura de devolver listas cuando corresponda y de castear `rating`
      a float si es posible.

    Args:
        p (Dict[str, Any]): Detalle del juego formateado (camelCase).

    Returns:
        Dict[str, Any]: Diccionario con claves de nuestro modelo `Game`.
    """

    rating: Optional[float] = None
    if p.get("rating") is not None:
        try:
            rating = float(p["rating"])
        except (TypeError, ValueError):
            rating = None

    def _lst(v: Any) -> List[Any]:
        return v if isinstance(v, list) else []

    return {
        # Identificadores / básicos
        "rawg_id": p.get("id"),
        "title": p.get("title") or "",
        "description": p.get("description") or None,
        "release_date": _to_date(p.get("releaseDate")),
        "image_url": p.get("imageUrl") or None,
        "rating": rating,

        # Colecciones (listas)
        "platforms": _lst(p.get("platforms")),
        "genres": _lst(p.get("genres")),
        "developers": _lst(p.get("developers")),
        "publishers": _lst(p.get("publishers")),
        "tags": _lst(p.get("tags")),
        "screenshots": _lst(p.get("screenshots")),
        "videos": _lst(p.get("videos")),
        "similar_games": _lst(p.get("similarGames")),

        # Metadatos adicionales
        "esrb_rating": p.get("esrbRating"),
        "metacritic_score": p.get("metacriticScore"),
        "metacritic_url": p.get("metacriticUrl"),
        "website": p.get("website"),
    }


async def upsert_from_formatted(db: AsyncSession, payload: Dict[str, Any]) -> Game:
    """
    Inserta o actualiza un registro de `Game` con datos formateados de RAWG.

    - Si no existe un `Game` con `rawg_id`, se crea.
    - Si existe, se actualizan los campos.
    - En ambos casos, se marca `fetched_at` con el momento actual.

    Args:
        db (AsyncSession): Sesión asíncrona de SQLAlchemy.
        payload (Dict[str, Any]): Detalle del juego (camelCase) tal y como
            lo devuelve `get_game_from_rawg()` → `format_game_detail`.

    Returns:
        Game: Instancia persistida (insertada o actualizada).
    """
    data = _map_formatted_detail(payload)
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


async def get_or_fetch_game(db: AsyncSession, rawg_id: int) -> Game:
    """
    Devuelve un `Game` desde la caché local si está “fresco” (TTL), o lo
    refresca desde RAWG en caso contrario.

    Flujo:
    1) Busca por `rawg_id` en la tabla `games`.
    2) Si existe y `fetched_at` > ahora - TTL → devuelve el caché.
    3) Si no existe o está caduco, llama a `get_game_from_rawg(rawg_id)`,
       mapea e inserta/actualiza con `upsert_from_formatted`, y devuelve.

    Args:
        db (AsyncSession): Sesión asíncrona de SQLAlchemy.
        rawg_id (int): Identificador del juego en RAWG.

    Returns:
        Game: Instancia lista para usar (caché o recién refrescada).
    """
    g = await _get_by_rawg_id(db, rawg_id)
    if g and g.fetched_at and (g.fetched_at > _utcnow() - CACHE_TTL):
        return g

    payload = await get_game_from_rawg(rawg_id)
    return await upsert_from_formatted(db, payload)
