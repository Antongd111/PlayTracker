import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.friendship import FriendshipStatus
from app.models.user import User
from app.services import friendship

pytestmark = pytest.mark.anyio("asyncio")


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


def test_pair_orders_correctly():
   assert friendship._pair(1, 2) == (1, 2)
   assert friendship._pair(5, 2) == (2, 5)
   assert friendship._pair(3, 3) == (3, 3)


async def test_send_request_creates_pending_friendship(db_session: AsyncSession):
   user1 = await _create_user(db_session, "alice")
   user2 = await _create_user(db_session, "bob")

   fr = await friendship.send_request(db_session, user1.id, user2.id)

   assert fr is not None
   assert fr.user_id_a < fr.user_id_b
   assert fr.requester_id == user1.id
   assert fr.status == FriendshipStatus.pending

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


async def test_accept_request_changes_status(db_session: AsyncSession):
   a = await _create_user(db_session, "carl")
   b = await _create_user(db_session, "dana")

   await friendship.send_request(db_session, a.id, b.id)
   accepted = await friendship.accept_request(db_session, b.id, a.id)

   assert accepted.status == FriendshipStatus.accepted
   assert accepted.responded_at is not None


async def test_accept_request_invalid_cases_return_none(db_session: AsyncSession):
   a = await _create_user(db_session, "e1")
   b = await _create_user(db_session, "e2")

   assert await friendship.accept_request(db_session, a.id, b.id) is None

   fr = await friendship.send_request(db_session, a.id, b.id)
   fr.status = FriendshipStatus.accepted
   await db_session.commit()
   assert await friendship.accept_request(db_session, b.id, a.id) is None

   fr = await friendship.send_request(db_session, a.id, b.id)
   assert await friendship.accept_request(db_session, a.id, b.id) is None


async def test_decline_request_sets_declined_status(db_session: AsyncSession):
   a = await _create_user(db_session, "declineA")
   b = await _create_user(db_session, "declineB")

   await friendship.send_request(db_session, a.id, b.id)
   declined = await friendship.decline_request(db_session, b.id, a.id)

   assert declined.status == FriendshipStatus.declined
   assert declined.responded_at is not None
