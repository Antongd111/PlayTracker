import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import review as service
from app.models.user import User
from app.models.game import Game
from app.models.user_game import UserGame


pytestmark = pytest.mark.anyio("asyncio")


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

async def _create_user(db: AsyncSession, username: str) -> User:
    u = User(
        email=f"{username}@example.com",
        username=username,
        hashed_password="fake",
        status="active",
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


async def _create_game(db: AsyncSession, rawg_id: int, title: str) -> Game:
    g = Game(rawg_id=rawg_id, title=title)
    db.add(g)
    await db.commit()
    await db.refresh(g)
    return g


async def _create_usergame(
    db: AsyncSession,
    user: User,
    game: Game,
    score: int = 7,
    notes: str = "ok",
    contains_spoilers: bool = False,
) -> UserGame:
    ug = UserGame(
        user_id=user.id,
        game_id=game.id,
        score=score,
        notes=notes,
        contains_spoilers=contains_spoilers,
        review_updated_at=datetime.utcnow(),
    )
    db.add(ug)
    await db.commit()
    await db.refresh(ug)
    return ug


# ----------------------------------------------------------------------
# upsert_review
# ----------------------------------------------------------------------

async def test_upsert_review_creates_or_updates_usergame(db_session: AsyncSession):
    user = await _create_user(db_session, "alice")
    game = await _create_game(db_session, 111, "Halo")

    # Crear review nueva
    ug = await service.upsert_review(
        db=db_session,
        user_id=user.id,
        game_id=game.rawg_id,
        score=9,
        notes="amazing",
        contains_spoilers=False,
    )

    assert ug is not None
    assert ug.score == 9
    assert ug.notes == "amazing"

    # Actualizar misma review
    updated = await service.upsert_review(
        db=db_session,
        user_id=user.id,
        game_id=game.rawg_id,
        score=6,
        notes="meh",
        contains_spoilers=True,
    )

    assert updated.id == ug.id
    assert updated.score == 6
    assert updated.contains_spoilers is True
    assert updated.review_updated_at >= ug.review_updated_at


# ----------------------------------------------------------------------
# get_game_reviews_stats
# ----------------------------------------------------------------------

async def test_get_game_reviews_stats_computes_average_and_count(db_session: AsyncSession):
    u1 = await _create_user(db_session, "p1")
    u2 = await _create_user(db_session, "p2")
    g = await _create_game(db_session, 222, "Zelda")

    await _create_usergame(db_session, u1, g, score=8)
    await _create_usergame(db_session, u2, g, score=6)

    avg, cnt = await service.get_game_reviews_stats(db_session, g.rawg_id)
    assert round(avg, 1) == 7.0
    assert cnt == 2


# ----------------------------------------------------------------------
# list_reviews_for_game
# ----------------------------------------------------------------------

async def test_list_reviews_for_game_returns_expected_structure(db_session: AsyncSession):
    viewer = await _create_user(db_session, "viewer")
    author = await _create_user(db_session, "author")
    g = await _create_game(db_session, 333, "FFVII")

    await _create_usergame(db_session, author, g, score=10, notes="masterpiece")

    rows = await service.list_reviews_for_game(
        db_session, g.rawg_id, viewer_user_id=viewer.id, limit=10
    )

    assert isinstance(rows, list)
    assert len(rows) == 1
    r = rows[0]

    assert r["user_id"] == author.id
    assert r["score"] == 10
    assert "likes_count" in r
    assert "liked_by_me" in r
    assert "username" in r


# ----------------------------------------------------------------------
# like_review / unlike_review (Todavía tengo que implementar correctamente esta funcionalidad)
# ----------------------------------------------------------------------

# async def test_like_and_unlike_review_flow(db_session: AsyncSession):
#     author = await _create_user(db_session, "author")
#     liker = await _create_user(db_session, "liker")
#     g = await _create_game(db_session, 444, "Elden Ring")

#     await _create_usergame(db_session, author, g, score=9)

#     ok = await service.like_review(
#         db_session,
#         liker_user_id=liker.id,
#         author_user_id=author.id,
#         game_id=g.rawg_id,
#     )
#     assert ok is True

#     # Unlike
#     await service.unlike_review(
#         db_session,
#         liker_user_id=liker.id,
#         author_user_id=author.id,
#         game_id=g.rawg_id,
#     )

#     # No debería lanzar error ni dejar likes
#     ok2 = await service.like_review(
#         db_session,
#         liker_user_id=liker.id,
#         author_user_id=author.id,
#         game_id=g.rawg_id,
#     )
#     assert ok2 is True
