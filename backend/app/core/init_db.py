import asyncio
import logging
from app.core.database import engine, Base
from app.models import user, user_game

logger = logging.getLogger(__name__)

async def init_db(retries: int = 30, delay: float = 1.0):
    for attempt in range(1, retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Base de datos inicializada correctamente.")
            return
        except Exception as e:
            logger.warning(f"Init DB intento {attempt}/{retries} fallido: {e}")
            if attempt == retries:
                logger.error("No se pudo inicializar la base de datos después de varios intentos.")
                raise
            await asyncio.sleep(delay)