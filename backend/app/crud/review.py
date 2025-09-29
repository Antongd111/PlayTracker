from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from sqlalchemy import select, func, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_game import UserGame
from app.models.user import User
from app.models.review_like import ReviewLike

# ---------- Actualizar/Crear reseña ----------
async def upsert_review(
    db: AsyncSession,
    user_id: int,
    game_rawg_id: int,
    score: Optional[int],
    notes: Optional[str],
    contains_spoilers: bool,
) -> UserGame:
    now = datetime.now(timezone.utc)

    q = select(UserGame).where(
        (UserGame.user_id == user_id) & (UserGame.game_rawg_id == game_rawg_id)
    )
    res = await db.execute(q)
    ug = res.scalar_one_or_none()

    if ug is None:
        ug = UserGame(
            user_id=user_id,
            game_rawg_id=game_rawg_id,
            status="wishlist",
        )
        db.add(ug)

    ug.score = score
    ug.notes = notes
    ug.contains_spoilers = bool(contains_spoilers)
    ug.review_updated_at = now

    await db.commit()
    await db.refresh(ug)
    return ug

# ---------- Métricas (media y conteo) ----------
async def get_game_reviews_stats(
    db: AsyncSession,
    game_rawg_id: int,
) -> tuple[Optional[float], int]:
    q = select(
        func.avg(UserGame.score).label("avg"),
        func.count().label("cnt"),
    ).where(
        (UserGame.game_rawg_id == game_rawg_id) & (UserGame.score.isnot(None))
    )
    res = await db.execute(q)
    avg, cnt = res.fetchone()
    return (float(avg) if avg is not None else None, int(cnt or 0))

# ---------- Listado de reseñas de un juego ----------
async def list_reviews_for_game(
    db: AsyncSession,
    game_rawg_id: int,
    viewer_user_id: int,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    likes_cnt_sq = (
        select(
            ReviewLike.review_user_id.label("ru"),
            ReviewLike.review_game_rawg_id.label("rg"),
            func.count().label("likes_count"),
        )
        .where(ReviewLike.review_game_rawg_id == game_rawg_id)
        .group_by(ReviewLike.review_user_id, ReviewLike.review_game_rawg_id)
        .subquery()
    )

    liked_by_me_sq = (
        select(
            ReviewLike.review_user_id.label("ru"),
            ReviewLike.review_game_rawg_id.label("rg"),
        )
        .where(
            (ReviewLike.liker_user_id == viewer_user_id) &
            (ReviewLike.review_game_rawg_id == game_rawg_id)
        )
        .subquery()
    )

    q = (
        select(
            UserGame.user_id,
            UserGame.game_rawg_id,
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
        .outerjoin(
            likes_cnt_sq,
            (likes_cnt_sq.c.ru == UserGame.user_id) &
            (likes_cnt_sq.c.rg == UserGame.game_rawg_id)
        )
        .outerjoin(
            liked_by_me_sq,
            (liked_by_me_sq.c.ru == UserGame.user_id) &
            (liked_by_me_sq.c.rg == UserGame.game_rawg_id)
        )
        .where(UserGame.game_rawg_id == game_rawg_id)
        .order_by(UserGame.review_updated_at.desc().nullslast())
        .limit(limit)
    )
    res = await db.execute(q)
    return res.mappings().all()

# ---------- Like / Unlike ----------
async def like_review(
    db: AsyncSession,
    liker_user_id: int,
    author_user_id: int,
    game_rawg_id: int,
) -> bool:
    exists_q = select(UserGame.user_id).where(
        (UserGame.user_id == author_user_id) &
        (UserGame.game_rawg_id == game_rawg_id)
    )
    if (await db.execute(exists_q)).scalar_one_or_none() is None:
        return False

    stmt = pg_insert(ReviewLike).values(
        review_user_id=author_user_id,
        review_game_rawg_id=game_rawg_id,
        liker_user_id=liker_user_id,
    ).on_conflict_do_nothing()

    await db.execute(stmt)
    await db.commit()
    return True

async def unlike_review(
    db: AsyncSession,
    liker_user_id: int,
    author_user_id: int,
    game_rawg_id: int,
) -> bool:
    res = await db.execute(
        delete(ReviewLike).where(
            (ReviewLike.review_user_id == author_user_id) &
            (ReviewLike.review_game_rawg_id == game_rawg_id) &
            (ReviewLike.liker_user_id == liker_user_id)
        )
    )
    await db.commit()
    return True
