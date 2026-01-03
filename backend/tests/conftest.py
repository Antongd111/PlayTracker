import os
import inspect
import pytest
from typing import AsyncGenerator, Iterable

from httpx import AsyncClient
try:
   from httpx import ASGITransport
except ImportError:
   ASGITransport = None

from asgi_lifespan import LifespanManager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
   AsyncSession,
   create_async_engine,
   async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from main import app
from app.core.dependencies import get_db
from app.core.database import Base

# --- DB de test ---
DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
   DATABASE_URL,
   echo=False,
   future=True,
   poolclass=NullPool,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(scope="session")
def anyio_backend():
   return "asyncio"


def _import_models_for_metadata() -> None:
   """
   Asegura que los modelos se importan para que Base.metadata conozca las tablas
   antes de create_all(). Si no se importan, Postgres dirá 'relation "users" does not exist'.
   """
   # Ajusta/añade imports aquí si tienes más modelos que deban existir en tests.
   import app.models.user  # noqa: F401
   import app.models.friendship  # noqa: F401


@pytest.fixture(scope="session")
async def setup_database():
   """
   Crea TODAS las tablas 1 vez por sesión de tests.
   No es autouse, porque si lo fuese rompería tests sync (pytest no ejecuta fixtures async en tests sync).
   """
   _import_models_for_metadata()

   async with engine.begin() as conn:
      await conn.run_sync(Base.metadata.create_all)

   yield

   async with engine.begin() as conn:
      await conn.run_sync(Base.metadata.drop_all)

   await engine.dispose()


async def _truncate_all_tables(session: AsyncSession) -> None:
   """
   Limpia la BD entre tests.
   - En Postgres: TRUNCATE ... CASCADE
   - En SQLite memory: DELETE por tabla
   """
   dialect = session.bind.dialect.name  # type: ignore[union-attr]

   tables: Iterable[str] = Base.metadata.tables.keys()

   if dialect == "postgresql":
      if not tables:
         return
      joined = ", ".join(f'"{t}"' for t in tables)
      await session.execute(text(f"TRUNCATE TABLE {joined} RESTART IDENTITY CASCADE"))
      await session.commit()
      return

   # Fallback genérico (SQLite / otros)
   for t in tables:
      await session.execute(text(f'DELETE FROM "{t}"'))
   await session.commit()


@pytest.fixture()
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
   """
   Sesión de BD por test.
   - Garantiza que las tablas existen (depende de setup_database).
   - Limpia tablas antes de cada test para aislamiento.
   - Usa una transacción por test y rollback al final.
   """
   async with engine.connect() as conn:
      trans = await conn.begin()
      session = SessionLocal(bind=conn)

      try:
         # Limpieza al inicio para que cada test arranque limpio
         await _truncate_all_tables(session)
         yield session
      finally:
         if session.in_transaction():
            await session.rollback()
         await session.close()
         await trans.rollback()


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


def pytest_report_teststatus(report, config):
   if report.when == "call":
      if report.passed:
         return report.outcome, "✅", "PASSED ✅"
      if report.failed:
         return report.outcome, "❌", "FAILED ❌"
      if report.skipped:
         return report.outcome, "⚠️", "SKIPPED ⚠️"
