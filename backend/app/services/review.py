from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from sqlalchemy import select, func, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_game import UserGame
from app.models.user import User
from app.models.review_like import ReviewLike
from app.models.game import Game

from app.services.game_cache import get_or_fetch_game


# ----------------------------------------------------------------------
# Upsert de reseña (crear/actualizar)
# ----------------------------------------------------------------------

async def upsert_review(
    db: AsyncSession,
    user_id: int,
    game_id: int,  # este sigue siendo el RAWG ID externo
    score: Optional[int],
    notes: Optional[str],
    contains_spoilers: bool,
) -> UserGame:
    """
    Crea o actualiza la reseña (score/notes/spoilers) de un usuario para un juego.
    Usa la caché local (tabla 'games') para asegurar integridad referencial.
    """

    now = datetime.now(timezone.utc)

    game = await get_or_fetch_game(db, game_id)
    await db.flush()

    q = select(UserGame).where(
        (UserGame.user_id == user_id) & (UserGame.game_id == game.id)
    )
    res = await db.execute(q)
    ug = res.scalar_one_or_none()

    if ug is None:
        ug = UserGame(
            user_id=user_id,
            game_id=game.id,
            status="wishlist",
        )
        db.add(ug)

    # Actualizar campos de reseña
    ug.score = score
    ug.notes = notes
    ug.contains_spoilers = bool(contains_spoilers)
    ug.review_updated_at = now

    await db.commit()
    await db.refresh(ug)
    return ug


# ----------------------------------------------------------------------
# Métricas agregadas de reseñas (media y conteo)
# ----------------------------------------------------------------------

async def get_game_reviews_stats(
    db: AsyncSession,
    game_id: int,
) -> tuple[Optional[float], int]:
    """
    Calcula la media de puntuación y el número de reseñas con puntuación para un juego.

    Args:
        db (AsyncSession): Sesión asíncrona de SQLAlchemy.
        game_id (int): Identificador del juego en RAWG.

    Returns:
        tuple[Optional[float], int]:
            - media (float o None si no hay puntuaciones)
            - conteo de reseñas con puntuación (int)
    """

    q = (
        select(
            func.avg(UserGame.score).label("avg"),
            func.count(UserGame.id).label("cnt"),
        )
        .join(Game, Game.id == UserGame.game_id)
        .where((Game.rawg_id == game_id) & (UserGame.score.isnot(None)))
    )

    res = await db.execute(q)
    avg, cnt = res.one_or_none() or (None, 0)
    return (float(avg) if avg is not None else None, int(cnt or 0))



# ----------------------------------------------------------------------
# Listado de reseñas de un juego (con likes y “liked_by_me”)
# ----------------------------------------------------------------------

async def list_reviews_for_game(
    db: AsyncSession,
    game_id: int,
    viewer_user_id: int,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Lista reseñas de un juego con metadatos (autor, avatar, likes y si el viewer le dio like).

    - Incluye `likes_count` por reseña usando una subconsulta agregada.
    - La bandera `liked_by_me` indica si el usuario `viewer_user_id` ha dado like
      a esa reseña.
    - Ordena por `review_updated_at` descendente (nulls last) y limita el resultado.

    Args:
        db (AsyncSession): Sesión asíncrona de SQLAlchemy.
        game_id (int): Identificador del juego en RAWG.
        viewer_user_id (int): ID del usuario que visualiza (para calcular `liked_by_me`).
        limit (int): Máximo de reseñas a devolver (por defecto 20).

    Returns:
        List[Dict[str, Any]]: Lista de filas mapeadas con:
            - user_id, game_id, score, notes, contains_spoilers, review_updated_at
            - username, avatar_url
            - likes_count (int)
            - liked_by_me (bool)
    """

    likes_cnt_sq = (
        select(
            ReviewLike.review_user_id.label("ru"),
            ReviewLike.review_game_id.label("rg"),
            func.count().label("likes_count"),
        )
        .where(ReviewLike.review_game_id == game_id)
        .group_by(ReviewLike.review_user_id, ReviewLike.review_game_id)
        .subquery()
    )

    liked_by_me_sq = (
        select(
            ReviewLike.review_user_id.label("ru"),
            ReviewLike.review_game_id.label("rg"),
        )
        .where(
            (ReviewLike.liker_user_id == viewer_user_id) &
            (ReviewLike.review_game_id == game_id)
        )
        .subquery()
    )

    q = (
        select(
            UserGame.user_id,
            UserGame.game_id,
            UserGame.score,
            UserGame.notes,
            UserGame.contains_spoilers,
            UserGame.review_updated_at,
            User.username,
            User.avatar_url,
            func.coalesce(likes_cnt_sq.c.likes_count, 0).label("likes_count"),
            (liked_by_me_sq.c.ru.isnot(None)).label("liked_by_me"),
        )
        .join(User, User.id == UserGame.user_id)
        .join(Game, Game.id == UserGame.game_id)  # ✅ join necesario
        .outerjoin(
            likes_cnt_sq,
            (likes_cnt_sq.c.ru == UserGame.user_id)
            & (likes_cnt_sq.c.rg == UserGame.game_id),
        )
        .outerjoin(
            liked_by_me_sq,
            (liked_by_me_sq.c.ru == UserGame.user_id)
            & (liked_by_me_sq.c.rg == UserGame.game_id),
        )
        .where(Game.rawg_id == game_id)  # ✅ usa RAWG ID externo
        .order_by(UserGame.review_updated_at.desc().nullslast())
        .limit(limit)
    )
    
    res = await db.execute(q)
    return res.mappings().all()


# ----------------------------------------------------------------------
# Likes de reseñas (like / unlike)
# ----------------------------------------------------------------------

async def like_review(
    db: AsyncSession,
    liker_user_id: int,
    author_user_id: int,
    game_id: int,
) -> bool:
    """
    Registra un 'like' de `liker_user_id` sobre la reseña de `author_user_id` y `game_id`.

    - Verifica primero que exista la reseña (registro en UserGame para el autor).
    - Inserta el like en `ReviewLike` de forma idempotente (ON CONFLICT DO NOTHING).

    Args:
        db (AsyncSession): Sesión asíncrona de SQLAlchemy.
        liker_user_id (int): Usuario que da like.
        author_user_id (int): Autor de la reseña.
        game_id (int): Juego al que pertenece la reseña.

    Returns:
        bool: `True` si se confirmó la operación (o ya existía el like),
              `False` si la reseña no existe.
    """

    exists_q = select(UserGame.user_id).where(
        (UserGame.user_id == author_user_id) &
        (UserGame.game_id == game_id)
    )
    if (await db.execute(exists_q)).scalar_one_or_none() is None:
        return False

    stmt = pg_insert(ReviewLike).values(
        review_user_id=author_user_id,
        review_game_id=game_id,
        liker_user_id=liker_user_id,
    ).on_conflict_do_nothing()

    await db.execute(stmt)
    await db.commit()
    return True


async def unlike_review(
    db: AsyncSession,
    liker_user_id: int,
    author_user_id: int,
    game_id: int,
) -> bool:
    """
    Elimina el 'like' de `liker_user_id` sobre la reseña de `author_user_id` y `game_id`.

    - Si el like no existía, la operación sigue siendo segura (idempotente).

    Args:
        db (AsyncSession): Sesión asíncrona de SQLAlchemy.
        liker_user_id (int): Usuario que quita el like.
        author_user_id (int): Autor de la reseña.
        game_id (int): Juego al que pertenece la reseña.

    Returns:
        bool: `True` tras confirmar la transacción (aunque no existiese el like previamente).
    """

    await db.execute(
        delete(ReviewLike).where(
            (ReviewLike.review_user_id == author_user_id) &
            (ReviewLike.review_game_id == game_id) &
            (ReviewLike.liker_user_id == liker_user_id)
        )
    )
    await db.commit()
    return True
