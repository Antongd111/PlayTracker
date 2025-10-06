# app/crud/friendship.py
from __future__ import annotations
from typing import List, Optional, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, delete

from app.models.friendship import Friendship, FriendshipStatus
from app.models.user import User


def _pair(u1: int, u2: int) -> Tuple[int, int]:
    """Normaliza el par para cumplir user_id_a < user_id_b."""
    return (u1, u2) if u1 < u2 else (u2, u1)


async def get_friendship(db: AsyncSession, u1: int, u2: int) -> Optional[Friendship]:
    a, b = _pair(u1, u2)
    q = select(Friendship).where(
        and_(Friendship.user_id_a == a, Friendship.user_id_b == b)
    )
    res = await db.execute(q)
    return res.scalar_one_or_none()


async def send_request(db: AsyncSession, me: int, to: int) -> Optional[Friendship]:
    if me == to:
        return None

    a, b = _pair(me, to)
    fr = await get_friendship(db, me, to)

    if fr is None:
        fr = Friendship(
            user_id_a=a,
            user_id_b=b,
            requester_id=me,
            status=FriendshipStatus.pending,
        )
        db.add(fr)
        await db.commit()
        await db.refresh(fr)
        return fr

    # Si estaba declined, reabrimos como pending con requester actual
    if fr.status == FriendshipStatus.declined:
        fr.status = FriendshipStatus.pending
        fr.requester_id = me
        fr.requested_at = datetime.utcnow()
        fr.responded_at = None
        fr.blocker_id = None
        await db.commit()
        await db.refresh(fr)
        return fr

    # Si ya existe (pending/accepted/blocked), no hacemos nada
    return None


async def accept_request(db: AsyncSession, me: int, from_user: int) -> Optional[Friendship]:
    fr = await get_friendship(db, me, from_user)
    if fr is None:
        return None
    if fr.status != FriendshipStatus.pending:
        return None
    # me debe ser el destinatario, no el requester
    if fr.requester_id == me:
        return None

    fr.status = FriendshipStatus.accepted
    fr.responded_at = datetime.utcnow()
    fr.blocker_id = None
    await db.commit()
    await db.refresh(fr)
    return fr


async def decline_request(db: AsyncSession, me: int, from_user: int) -> Optional[Friendship]:
    fr = await get_friendship(db, me, from_user)
    if fr is None:
        return None
    if fr.status != FriendshipStatus.pending:
        return None
    if fr.requester_id == me:
        return None

    fr.status = FriendshipStatus.declined
    fr.responded_at = datetime.utcnow()
    fr.blocker_id = None
    await db.commit()
    await db.refresh(fr)
    return fr


async def unfriend(db: AsyncSession, me: int, other: int) -> Optional[Friendship]:
    fr = await get_friendship(db, me, other)
    if fr is None:
        return None
    if fr.status != FriendshipStatus.accepted:
        return None

    # Igual que tu delete_user_game: devolvemos la entidad y luego borramos
    await db.delete(fr)
    await db.commit()
    return fr


async def block_user(db: AsyncSession, me: int, other: int) -> Friendship:
    fr = await get_friendship(db, me, other)
    if fr is None:
        a, b = _pair(me, other)
        fr = Friendship(
            user_id_a=a,
            user_id_b=b,
            requester_id=me,  # arbitrario, pero consistente
            status=FriendshipStatus.blocked,
            blocker_id=me,
            responded_at=datetime.utcnow(),
        )
        db.add(fr)
        await db.commit()
        await db.refresh(fr)
        return fr

    fr.status = FriendshipStatus.blocked
    fr.blocker_id = me
    fr.responded_at = datetime.utcnow()
    await db.commit()
    await db.refresh(fr)
    return fr

async def cancel_request(db: AsyncSession, me: int, to: int) -> Optional[Friendship]:
    """
    Cancela (elimina) una solicitud PENDING que yo he enviado a 'to'.
    Devuelve la entidad eliminada si existía, o None si no había nada que cancelar.
    """
    fr = await get_friendship(db, me, to)
    if fr is None:
        return None
    # Debe estar pendiente y ser YO el requester
    if fr.status != FriendshipStatus.pending:
        return None
    if fr.requester_id != me:
        return None

    await db.delete(fr)
    await db.commit()
    return fr


async def list_friends(db: AsyncSession, me: int) -> List[User]:
    # Devuelve objetos User de los amigos aceptados
    # amigo = el otro extremo del par
    q = (
        select(User)
        .join(
            Friendship,
            or_(
                and_(Friendship.user_id_a == me, User.id == Friendship.user_id_b),
                and_(Friendship.user_id_b == me, User.id == Friendship.user_id_a),
            ),
        )
        .where(Friendship.status == FriendshipStatus.accepted)
        .order_by(User.username.asc())
    )
    res = await db.execute(q)
    return res.scalars().all()


async def list_incoming_requests(db: AsyncSession, me: int):
    # solicitudes donde me NO soy requester y status=pending
    q = (
        select(
            Friendship.requester_id,
            User.id.label("other_id"),
            User.username,
            User.avatar_url,
            Friendship.status,
            Friendship.requested_at,
        )
        .select_from(Friendship)
        .join(
            User,
            User.id == Friendship.requester_id,
        )
        .where(
            and_(
                Friendship.status == FriendshipStatus.pending,
                Friendship.requester_id != me,
                or_(Friendship.user_id_a == me, Friendship.user_id_b == me),
            )
        )
        .order_by(Friendship.requested_at.desc())
    )
    res = await db.execute(q)
    return res.mappings().all()


async def list_outgoing_requests(db: AsyncSession, me: int):
    # solicitudes donde YO soy requester y status=pending
    # el otro usuario es el opuesto del par
    q = (
        select(
            Friendship.requester_id,
            User.id.label("other_id"),
            User.username,
            User.avatar_url,
            Friendship.status,
            Friendship.requested_at,
        )
        .select_from(Friendship)
        .join(
            User,
            or_(
                and_(Friendship.user_id_a == me, User.id == Friendship.user_id_b),
                and_(Friendship.user_id_b == me, User.id == Friendship.user_id_a),
            ),
        )
        .where(
            and_(
                Friendship.status == FriendshipStatus.pending,
                Friendship.requester_id == me,
                or_(Friendship.user_id_a == me, Friendship.user_id_b == me),
            )
        )
        .order_by(Friendship.requested_at.desc())
    )
    res = await db.execute(q)
    return res.mappings().all()
