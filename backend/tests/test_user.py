import pytest

from app.schemas.user import UserCreate
from app.services.user import create_user, get_user, pwd_context
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.anyio("asyncio")


async def test_create_user_persists_and_hashes_password(db_session: AsyncSession):
    """
    Debe crear el usuario, persistirlo en la BD y hashear la contraseña.
    """
    payload = UserCreate(
        email="test_user@example.com",
        username="test_user",
        password="super-secret",
        status="active",
        avatar_url=None,
    )

    # Act
    created: User = await create_user(db_session, payload)

    # Assert: se ha asignado ID (persistido)
    assert created.id is not None

    # Assert: campos básicos iguales a lo enviado
    assert created.email == payload.email
    assert created.username == payload.username
    assert created.status == payload.status
    assert created.avatar_url == payload.avatar_url
    assert created.favorite_rawg_game_id == None

    # Assert: la contraseña está hasheada (no es igual a la plain)
    assert created.hashed_password != payload.password
    assert pwd_context.verify(payload.password, created.hashed_password)

    # Assert extra: puede recuperarse con get_user tras commit/refresh
    fetched = await get_user(db_session, created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.email == payload.email
    assert fetched.username == payload.username