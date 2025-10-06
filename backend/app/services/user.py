from __future__ import annotations
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from passlib.context import CryptContext

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Helpers --------------------------------------------------------------------

ALLOWED_UPDATE_FIELDS = {
    "email",
    "username",
    "status",
    "avatar_url",
    "favorite_rawg_game_id",
}

def _filter_updatable_fields(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in payload.items() if k in ALLOWED_UPDATE_FIELDS}


# Funciones ------------------------------------------------------------------

async def get_users(db: AsyncSession, q: Optional[str] = None) -> List[User]:
    if q:
        result = await db.execute(
            select(User).where(
                or_(User.username.ilike(f"%{q}%"), User.email.ilike(f"%{q}%"))
            )
        )
        return result.scalars().all()

    result = await db.execute(select(User))
    return result.scalars().all()


async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    hashed_pw = pwd_context.hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_pw,
        status=user.status,
        avatar_url=user.avatar_url,
        favorite_rawg_game_id=getattr(user, "favorite_rawg_game_id", None),
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate) -> Optional[User]:
    # Cargar
    result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = result.scalar_one_or_none()
    if not user:
        return None

    data = user_update.dict(exclude_unset=True)

    # Resto de campos permitidos
    for field, value in _filter_updatable_fields(data).items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = result.scalar_one_or_none()
    if not user:
        return None
    await db.delete(user)
    await db.commit()
    return user




# async def get_friends_games(
#     db: AsyncSession,
#     user_id: int,
#     limit: int = 10
# ) -> List[GamePreview]:
#     """
#     Devuelve hasta `limit` GamePreview de juegos de los amigos aceptados del usuario,
#     tomando juegos con estado 'Completado', agrupados por game_rawg_id, en orden aleatorio.
#     """
#     stmt = (
#         select(
#             UserGame.game_rawg_id.label("id"),
#             func.max(UserGame.game_title).label("title"),
#             func.max(UserGame.image_url).label("imageUrl"),
#             func.max(UserGame.release_year).label("year"),
#         )
#         .join(
#             Friendship,
#             or_(
#                 and_(Friendship.user_id_a == user_id, UserGame.user_id == Friendship.user_id_b),
#                 and_(Friendship.user_id_b == user_id, UserGame.user_id == Friendship.user_id_a),
#             ),
#         )
#         .where(
#             Friendship.status == FriendshipStatus.accepted,
#             UserGame.status == "Completado",
#         )
#         .group_by(UserGame.game_rawg_id)
#         .order_by(func.random())
#         .limit(limit)
#     )

#     rows = await db.execute(stmt)
#     return [GamePreview(**m) for m in rows.mappings().all()]


# async def set_favorite(db: AsyncSession, user_id: int, favorite_rawg_game_id: Optional[int]):
#     result = await db.execute(select(User).where(User.id == user_id))
#     user = result.scalar_one_or_none()
#     if not user:
#         return None

#     user.favorite_rawg_game_id = favorite_rawg_game_id
#     await db.commit()
#     await db.refresh(user)
#     return user