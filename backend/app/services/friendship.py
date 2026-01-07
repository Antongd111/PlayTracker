# app/crud/friendship.py
from __future__ import annotations
from typing import List, Optional, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.friendship import Friendship, FriendshipStatus
from app.models.user import User


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _pair(u1: int, u2: int) -> Tuple[int, int]:
    """
    Normaliza el par (u1, u2) para que siempre cumpla user_id_a < user_id_b.

    Esto evita duplicados y simplifica las consultas al almacenar las amistades
    en una sola fila por par de usuarios (independiente del orden).

    Args:
        u1 (int): Primer usuario.
        u2 (int): Segundo usuario.

    Returns:
        Tuple[int, int]: Par ordenado (menor, mayor).
    """
    return (u1, u2) if u1 < u2 else (u2, u1)


# ----------------------------------------------------------------------
# Consultas y transiciones de estado
# ----------------------------------------------------------------------

async def get_friendship(db: AsyncSession, u1: int, u2: int) -> Optional[Friendship]:
    """
    Recupera (si existe) la relación de amistad para el par de usuarios dado.

    Args:
        db (AsyncSession): Sesión asíncrona de SQLAlchemy.
        u1 (int): ID del primer usuario.
        u2 (int): ID del segundo usuario.

    Returns:
        Optional[Friendship]: Entidad Friendship o None si no existe.
    """
    a, b = _pair(u1, u2)
    q = select(Friendship).where(
        and_(Friendship.user_id_a == a, Friendship.user_id_b == b)
    )
    res = await db.execute(q)
    return res.scalar_one_or_none()


async def send_request(db: AsyncSession, me: int, to: int) -> Optional[Friendship]:
    """
    Envía una solicitud de amistad de `me` a `to`.

    - Si no existe relación previa, crea una nueva con estado `pending`.
    - Si existía como `declined`, la reabre como `pending` (nuevo requester = `me`).
    - Si la relación ya es `pending/accepted/blocked`, no hace nada y devuelve None.
    - Si `me == to`, devuelve None (no tiene sentido auto-solicitarse).

    Args:
        db (AsyncSession): Sesión asíncrona de SQLAlchemy.
        me (int): Usuario que envía la solicitud.
        to (int): Usuario destinatario de la solicitud.

    Returns:
        Optional[Friendship]: Entidad creada/actualizada o None si no procede.
    """
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

    if fr.status == FriendshipStatus.declined:
        fr.status = FriendshipStatus.pending
        fr.requester_id = me
        fr.requested_at = datetime.utcnow()
        fr.responded_at = None
        fr.blocker_id = None
        await db.commit()
        await db.refresh(fr)
        return fr

    return None


async def accept_request(
    db: AsyncSession, 
    me: int, 
    from_user_id: Optional[int] = None, 
    friendship_id: Optional[int] = None
) -> Optional[Friendship]:
    """
    Acepta una solicitud. Puede buscarse por friendship_id o por el par de usuarios.
    """
    if friendship_id:
        fr = await db.get(Friendship, friendship_id)
    elif from_user_id:
        fr = await get_friendship(db, me, from_user_id)
    else:
        return None

    if fr is None or fr.status != FriendshipStatus.pending or fr.requester_id == me:
        return None

    fr.status = FriendshipStatus.accepted
    fr.responded_at = datetime.utcnow()
    fr.blocker_id = None
    await db.commit()
    await db.refresh(fr)
    return fr


async def decline_request(
    db: AsyncSession, 
    me: int, 
    from_user_id: Optional[int] = None, 
    friendship_id: Optional[int] = None
) -> Optional[Friendship]:
    """
    Rechaza una solicitud pendiente.
    """
    if friendship_id:
        fr = await db.get(Friendship, friendship_id)
    elif from_user_id:
        fr = await get_friendship(db, me, from_user_id)
    else:
        return None

    if fr is None or fr.status != FriendshipStatus.pending or fr.requester_id == me:
        return None

    fr.status = FriendshipStatus.declined
    fr.responded_at = datetime.utcnow()
    fr.blocker_id = None
    await db.commit()
    await db.refresh(fr)
    return fr


async def unfriend(
    db: AsyncSession, 
    me: int, 
    other_user_id: Optional[int] = None, 
    friendship_id: Optional[int] = None
) -> Optional[Friendship]:
    """
    Elimina una amistad (accepted) o cancela una solicitud propia (pending).
    """
    if friendship_id:
        fr = await db.get(Friendship, friendship_id)
    elif other_user_id:
        fr = await get_friendship(db, me, other_user_id)
    else:
        return None

    if fr is None:
        return None
        
    # Solo podemos borrar si está aceptada, o si es una solicitud pendiente enviada por mí
    is_accepted = fr.status == FriendshipStatus.accepted
    is_my_pending = fr.status == FriendshipStatus.pending and fr.requester_id == me
    
    if not (is_accepted or is_my_pending):
        return None

    await db.delete(fr)
    await db.commit()
    return fr


async def block_user(
    db: AsyncSession, 
    me: int, 
    other_user_id: Optional[int] = None, 
    friendship_id: Optional[int] = None
) -> Optional[Friendship]:
    """
    Bloquea a un usuario.
    """
    if friendship_id:
        fr = await db.get(Friendship, friendship_id)
    elif other_user_id:
        fr = await get_friendship(db, me, other_user_id)
        if fr is None:
            # Si no hay relación, creamos una nueva directamente bloqueada
            a, b = _pair(me, other_user_id)
            fr = Friendship(
                user_id_a=a, user_id_b=b,
                requester_id=me, status=FriendshipStatus.blocked,
                blocker_id=me, responded_at=datetime.utcnow()
            )
            db.add(fr)
            await db.commit()
            await db.refresh(fr)
            return fr
    else:
        return None

    if fr:
        fr.status = FriendshipStatus.blocked
        fr.blocker_id = me
        fr.responded_at = datetime.utcnow()
        await db.commit()
        await db.refresh(fr)
    return fr


async def cancel_request(db: AsyncSession, me: int, to: int) -> Optional[Friendship]:
    """
    Cancela (elimina) una solicitud PENDING que `me` ha enviado a `to`.

    Reglas:
    - Debe existir en estado `pending`.
    - `me` debe ser el `requester_id`.

    Args:
        db (AsyncSession): Sesión asíncrona de SQLAlchemy.
        me (int): Usuario que cancela la solicitud (debe ser requester).
        to (int): Destinatario de la solicitud.

    Returns:
        Optional[Friendship]: Entidad eliminada o None si no procede.
    """
    fr = await get_friendship(db, me, to)
    if fr is None:
        return None
    if fr.status != FriendshipStatus.pending:
        return None
    if fr.requester_id != me:
        return None

    await db.delete(fr)
    await db.commit()
    return fr


# ----------------------------------------------------------------------
# Listados
# ----------------------------------------------------------------------

async def list_friends(db: AsyncSession, me: int) -> List[User]:
    """
    Devuelve la lista de usuarios con los que `me` mantiene una amistad aceptada.

    Args:
        db (AsyncSession): Sesión asíncrona de SQLAlchemy.
        me (int): Usuario cuyo listado de amigos se solicita.

    Returns:
        List[User]: Colección de objetos User ordenados por username ascendente.
    """
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
    """
    Lista las solicitudes PENDING que ha recibido `me` (entrantes).

    Devuelve un mapeo con datos del solicitante (username, avatar) y metadatos de la
    solicitud.

    Args:
        db (AsyncSession): Sesión asíncrona de SQLAlchemy.
        me (int): Usuario destinatario.

    Returns:
        List[Mapping[str, Any]]: Filas mapeadas con requester y metadata.
    """
    q = (
        select(
            Friendship.id.label("friendship_id"),
            Friendship.requester_id,
            User.id.label("other_id"),
            User.username,
            User.avatar_url,
            Friendship.status,
            Friendship.requested_at,
        )
        .select_from(Friendship)
        .join(User, User.id == Friendship.requester_id)
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
    """
    Lista las solicitudes PENDING que ha enviado `me` (salientes).

    Devuelve un mapeo con datos del otro usuario y metadatos de la solicitud.

    Args:
        db (AsyncSession): Sesión asíncrona de SQLAlchemy.
        me (int): Usuario solicitante (requester).

    Returns:
        List[Mapping[str, Any]]: Filas mapeadas con el otro usuario y metadata.
    """
    q = (
        select(
            Friendship.id.label("friendship_id"),
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
