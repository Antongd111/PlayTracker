from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import select, and_, or_, func
from sqlalchemy import update, delete
from typing import List
from app.models.user import User
from app.models.user_game import UserGame
from app.schemas.user import UserCreate, UserUpdate
from passlib.context import CryptContext
from typing import Optional

from app.models.user_game import UserGame
from app.models.friendship import Friendship, FriendshipStatus
from app.schemas.game import GamePreview

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def get_users(db: AsyncSession):
    result = await db.execute(select(User))
    return result.scalars().all()

async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user: UserCreate):
    hashed_pw = pwd_context.hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_pw,
        status=user.status,
        avatar_url=user.avatar_url
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None

    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user

async def delete_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        await db.delete(user)
        await db.commit()
    return user

async def search_users(db: AsyncSession, query: str):
    result = await db.execute(
        select(User).where(
            or_(
                User.username.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%")
            )
        )
    )
    return result.scalars().all()


async def get_friends_games(
    db: AsyncSession,
    user_id: int,
    limit: int = 10
) -> List[GamePreview]:
    """
    Devuelve hasta `limit` GamePreview de juegos de los amigos aceptados del usuario,
    tomando juegos con estado 'Completado', agrupados por game_rawg_id, en orden aleatorio.
    """
    stmt = (
        select(
            UserGame.game_rawg_id.label("id"),
            func.max(UserGame.game_title).label("title"),
            func.max(UserGame.image_url).label("imageUrl"),
            func.max(UserGame.release_year).label("year"),
        )
        .join(
            Friendship,
            or_(
                and_(Friendship.user_id_a == user_id, UserGame.user_id == Friendship.user_id_b),
                and_(Friendship.user_id_b == user_id, UserGame.user_id == Friendship.user_id_a),
            ),
        )
        .where(
            Friendship.status == FriendshipStatus.accepted,
            UserGame.status == "Completado",
        )
        .group_by(UserGame.game_rawg_id)
        .order_by(func.random())
        .limit(limit)
    )

    rows = await db.execute(stmt)
    return [GamePreview(**m) for m in rows.mappings().all()]

async def set_favorite(db: AsyncSession, user_id: int, favorite_rawg_game_id: Optional[int]):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None

    user.favorite_rawg_game_id = favorite_rawg_game_id
    await db.commit()
    await db.refresh(user)
    return user