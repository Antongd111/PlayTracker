import os
import asyncio
import inspect
import pytest
from typing import AsyncGenerator

from httpx import AsyncClient
try:
    from httpx import ASGITransport
except ImportError:
    ASGITransport = None

from asgi_lifespan import LifespanManager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import close_all_sessions

from main import app
from app.core.dependencies import get_db
from app.core.database import Base

# --- DB de test ---
DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(DATABASE_URL, echo=False, future=True, poolclass=NullPool)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

""" Creación de loop de eventos para tests asíncronos """
@pytest.fixture(scope="session", autouse=True)
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

""" Limpieza y preparación de la base de datos antes de cada test """
@pytest.fixture(scope="function", autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield

""" Creación de la sesión de base de datos para los tests """
@pytest.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine.connect() as conn:
        trans = await conn.begin()
        session = SessionLocal(bind=conn)
        try:
            yield session
        finally:
            if session.in_transaction():
                await session.rollback()
            await session.close()
            await trans.rollback()

""" Cliente HTTP asíncrono para tests """
@pytest.fixture()
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session
    app.dependency_overrides[get_db] = _override_get_db

    supports_app_param = "app" in inspect.signature(AsyncClient.__init__).parameters
    try:
        if supports_app_param:
            async with LifespanManager(app):
                async with AsyncClient(app=app, base_url="http://test") as ac:
                    yield ac
        else:
            transport = ASGITransport(app=app) if ASGITransport else None
            async with LifespanManager(app):
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    yield ac
    finally:
        app.dependency_overrides.clear()

""" Configuración de AnyIO para tests asíncronos """
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

""" Personalización de los reportes de pytest """
def pytest_report_teststatus(report, config):
    if report.when == "call":
        if report.passed:
            return report.outcome, "✅", "PASSED ✅"
        if report.failed:
            return report.outcome, "❌", "FAILED ❌"
        if report.skipped:
            return report.outcome, "⚠️", "SKIPPED ⚠️"
