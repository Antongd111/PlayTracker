import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.friendship import FriendshipStatus
from app.models.user import User
from app.services import friendship


pytestmark = pytest.mark.anyio("asyncio")


async def _create_user(db: AsyncSession, username: str) -> User:
    """Crea un usuario auxiliar para los tests."""
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


# ----------------------------------------------------------------------
# _pair
# ----------------------------------------------------------------------

def test_pair_orders_correctly():
    assert friendship._pair(1, 2) == (1, 2)
    assert friendship._pair(5, 2) == (2, 5)
    assert friendship._pair(3, 3) == (3, 3)


# ----------------------------------------------------------------------
# send_request
# ----------------------------------------------------------------------

async def test_send_request_creates_pending_friendship(db_session: AsyncSession):
    user1 = await _create_user(db_session, "alice")
    user2 = await _create_user(db_session, "bob")

    fr = await friendship.send_request(db_session, user1.id, user2.id)

    assert fr is not None
    assert fr.user_id_a < fr.user_id_b
    assert fr.requester_id == user1.id
    assert fr.status == FriendshipStatus.pending

    # Se puede recuperar correctamente
    fetched = await friendship.get_friendship(db_session, user1.id, user2.id)
    assert fetched is not None
    assert fetched.id == fr.id


async def test_send_request_to_self_returns_none(db_session: AsyncSession):
    user = await _create_user(db_session, "solo")
    fr = await friendship.send_request(db_session, user.id, user.id)
    assert fr is None


async def test_send_request_revives_declined(db_session: AsyncSession):
    a = await _create_user(db_session, "a")
    b = await _create_user(db_session, "b")

    fr1 = await friendship.send_request(db_session, a.id, b.id)
    fr1.status = FriendshipStatus.declined
    await db_session.commit()

    revived = await friendship.send_request(db_session, b.id, a.id)
    assert revived.status == FriendshipStatus.pending
    assert revived.requester_id == b.id
    assert revived.responded_at is None


# ----------------------------------------------------------------------
# accept_request / decline_request
# ----------------------------------------------------------------------

async def test_accept_request_changes_status(db_session: AsyncSession):
    a = await _create_user(db_session, "carl")
    b = await _create_user(db_session, "dana")

    fr = await friendship.send_request(db_session, a.id, b.id)
    accepted = await friendship.accept_request(db_session, b.id, a.id)

    assert accepted.status == FriendshipStatus.accepted
    assert accepted.responded_at is not None


async def test_accept_request_invalid_cases_return_none(db_session: AsyncSession):
    a = await _create_user(db_session, "e1")
    b = await _create_user(db_session, "e2")

    # Sin relación
    assert await friendship.accept_request(db_session, a.id, b.id) is None

    # Ya aceptada
    fr = await friendship.send_request(db_session, a.id, b.id)
    fr.status = FriendshipStatus.accepted
    await db_session.commit()
    assert await friendship.accept_request(db_session, b.id, a.id) is None

    # requester no puede aceptarse a sí mismo
    fr = await friendship.send_request(db_session, a.id, b.id)
    assert await friendship.accept_request(db_session, a.id, b.id) is None


async def test_decline_request_sets_declined_status(db_session: AsyncSession):
    a = await _create_user(db_session, "declineA")
    b = await _create_user(db_session, "declineB")

    fr = await friendship.send_request(db_session, a.id, b.id)
    declined = await friendship.decline_request(db_session, b.id, a.id)

    assert declined.status == FriendshipStatus.declined
    assert declined.responded_at is not None


# ----------------------------------------------------------------------
# unfriend
# ----------------------------------------------------------------------

async def test_unfriend_deletes_accepted_friendship(db_session: AsyncSession):
    a = await _create_user(db_session, "tom")
    b = await _create_user(db_session, "jerry")

    fr = await friendship.send_request(db_session, a.id, b.id)
    await friendship.accept_request(db_session, b.id, a.id)

    deleted = await friendship.unfriend(db_session, a.id, b.id)
    assert deleted is not None

    # Ya no debe existir en la BD
    fr2 = await friendship.get_friendship(db_session, a.id, b.id)
    assert fr2 is None


# ----------------------------------------------------------------------
# block_user
# ----------------------------------------------------------------------

async def test_block_user_creates_or_updates_block(db_session: AsyncSession):
    u1 = await _create_user(db_session, "mark")
    u2 = await _create_user(db_session, "john")

    # Caso nuevo
    fr = await friendship.block_user(db_session, u1.id, u2.id)
    assert fr.status == FriendshipStatus.blocked
    assert fr.blocker_id == u1.id

    # Caso existente: actualizar
    fr2 = await friendship.block_user(db_session, u2.id, u1.id)
    assert fr2.status == FriendshipStatus.blocked
    assert fr2.blocker_id == u2.id


# ----------------------------------------------------------------------
# cancel_request
# ----------------------------------------------------------------------

async def test_cancel_request_deletes_pending_request(db_session: AsyncSession):
    a = await _create_user(db_session, "cancelA")
    b = await _create_user(db_session, "cancelB")

    fr = await friendship.send_request(db_session, a.id, b.id)
    deleted = await friendship.cancel_request(db_session, a.id, b.id)

    assert deleted is not None
    remaining = await friendship.get_friendship(db_session, a.id, b.id)
    assert remaining is None


# ----------------------------------------------------------------------
# list_friends / list_incoming_requests / list_outgoing_requests
# ----------------------------------------------------------------------

async def test_list_friends_returns_only_accepted(db_session: AsyncSession):
    a = await _create_user(db_session, "f1")
    b = await _create_user(db_session, "f2")
    c = await _create_user(db_session, "f3")

    await friendship.send_request(db_session, a.id, b.id)
    await friendship.accept_request(db_session, b.id, a.id)
    await friendship.send_request(db_session, a.id, c.id)

    friends = await friendship.list_friends(db_session, a.id)
    assert len(friends) == 1
    assert friends[0].username == "f2"


async def test_list_incoming_and_outgoing_requests(db_session: AsyncSession):
    sender = await _create_user(db_session, "sender")
    receiver = await _create_user(db_session, "receiver")

    await friendship.send_request(db_session, sender.id, receiver.id)

    incoming = await friendship.list_incoming_requests(db_session, receiver.id)
    outgoing = await friendship.list_outgoing_requests(db_session, sender.id)

    assert len(incoming) == 1
    assert len(outgoing) == 1
    assert incoming[0]["username"] == "sender"
    assert outgoing[0]["username"] == "receiver"
