# app/services/user_game.py
from __future__ import annotations
from typing import Optional, List, Any, Dict
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.user_game import UserGame
from app.models.game import Game
from app.schemas.user_game import UserGameCreate, UserGameUpdate
from app.services.game import get_game   # ← NUEVO servicio unificado


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _to_out(ug: UserGame, g: Game) -> Dict[str, Any]:
   """
   Mapea (UserGame + Game) al DTO de salida (UserGameOut).
   """
   release_date = g.release_date.isoformat() if g.release_date else None
   release_year = g.release_date.year if g.release_date else None

   return {
      "id": ug.id,
      "userId": ug.user_id,
      "gameRawgId": g.rawg_id,

      "gameTitle": g.title,
      "imageUrl": g.image_url,
      "releaseYear": release_year,

      "status": ug.status,
      "score": ug.score,
      "notes": ug.notes,
      "addedAt": ug.added_at,
      "reviewUpdatedAt": ug.review_updated_at,
      "containsSpoilers": ug.contains_spoilers,
   }


async def _get_join_row(db: AsyncSession, user_id: int, rawg_id: int) -> Optional[tuple[UserGame, Game]]:
   """
   Recupera (UserGame, Game) por (user_id, RAWG ID).
   """
   q = (
      select(UserGame, Game)
      .join(Game, Game.id == UserGame.game_id)
      .where(and_(UserGame.user_id == user_id, Game.rawg_id == rawg_id))
   )
   return (await db.execute(q)).first()


# -----------------------------------------------------------------------------
# Lecturas
# -----------------------------------------------------------------------------

async def get_user_games(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
   q = (
      select(UserGame, Game)
      .join(Game, Game.id == UserGame.game_id)
      .where(UserGame.user_id == user_id)
      .order_by(UserGame.added_at.desc())
   )
   rows = (await db.execute(q)).all()
   return [_to_out(ug, g) for (ug, g) in rows]


async def get_user_game(db: AsyncSession, user_id: int, rawg_id: int) -> Optional[Dict[str, Any]]:
   row = await _get_join_row(db, user_id, rawg_id)
   if not row:
      return None
   ug, g = row
   return _to_out(ug, g)


# -----------------------------------------------------------------------------
# Escrituras
# -----------------------------------------------------------------------------

async def create_user_game(db: AsyncSession, user_id: int, data: UserGameCreate) -> Dict[str, Any]:
   """
   1) Garantiza que el juego existe en `games` (creándolo/actualizándolo desde RAWG).
   2) Crea la relación UserGame.
   3) Devuelve DTO con previews del juego.
   """
   payload = data.model_dump(exclude_unset=True, by_alias=True)
   rawg_id = payload.get("gameRawgId")
   if rawg_id is None:
      raise ValueError("Se requiere gameRawgId (RAWG ID)")

   # Nueva función unificada
   g = await get_game(db, rawg_id)
   await db.flush()

   ug = UserGame(
      user_id=user_id,
      game_id=g.id,
      status=payload.get("status"),
      score=payload.get("score"),
      notes=payload.get("notes"),
      contains_spoilers=False,
   )

   db.add(ug)
   await db.commit()
   await db.refresh(ug)

   return _to_out(ug, g)


async def update_user_game(db: AsyncSession, user_id: int, rawg_id: int, data: UserGameUpdate) -> Optional[Dict[str, Any]]:
   row = await _get_join_row(db, user_id, rawg_id)
   if not row:
      return None

   ug, g = row
   changes = data.model_dump(exclude_unset=True, by_alias=True)

   if "status" in changes:
      ug.status = changes["status"]
   if "score" in changes:
      ug.score = changes["score"]
   if "notes" in changes:
      ug.notes = changes["notes"]
   if "containsSpoilers" in changes and changes["containsSpoilers"] is not None:
      ug.contains_spoilers = bool(changes["containsSpoilers"])

   if any(k in changes for k in ("score", "notes", "containsSpoilers")):
      ug.review_updated_at = datetime.now(timezone.utc)

   await db.commit()
   await db.refresh(ug)

   return _to_out(ug, g)


async def delete_user_game(db: AsyncSession, user_id: int, rawg_id: int) -> bool:
   q = (
      select(UserGame)
      .join(Game, Game.id == UserGame.game_id)
      .where(and_(UserGame.user_id == user_id, Game.rawg_id == rawg_id))
   )

   ug = (await db.execute(q)).scalar_one_or_none()
   if not ug:
      return False

   await db.delete(ug)
   await db.commit()
   return True
