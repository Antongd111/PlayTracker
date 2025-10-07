from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user_game import UserGame
from app.schemas.user_game import UserGameCreate, UserGameUpdate
from app.core.config import settings

import httpx

RAWG_API_KEY = settings.RAWG_API_KEY


# Helpers --------------------------------------------------------------------

async def _fetch_rawg_preview(rawg_id: int) -> Optional[dict]:
    """
    Recupera información básica de un videojuego desde la API de RAWG.

    Si existe una API key válida, consulta el endpoint de RAWG y devuelve un
    diccionario con el título, imagen y año de lanzamiento del juego.
    En caso de error o falta de API key, devuelve `None`.

    Args:
        rawg_id (int): Identificador del juego en la API de RAWG.

    Returns:
        Optional[dict]: Diccionario con los campos `game_title`, `image_url` y
        `release_year` o `None` si la consulta falla.
    """
    
    if not RAWG_API_KEY:
        return None

    url = f"https://api.rawg.io/api/games/{rawg_id}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, params={"key": RAWG_API_KEY})
            r.raise_for_status()
            data = r.json()

        title = data.get("name") or ""
        img = data.get("background_image")
        rel = data.get("released")  # formato "YYYY-MM-DD"
        year = int(rel.split("-")[0]) if rel else None

        return {"game_title": title, "image_url": img, "release_year": year}

    except Exception:
        return None


# Funciones ------------------------------------------------------------------

async def get_user_games(db: AsyncSession, user_id: int) -> List[UserGame]:
    """
    Devuelve todos los juegos asociados a un usuario específico.

    Args:
        db (AsyncSession): Sesión asíncrona de SQLAlchemy.
        user_id (int): ID del usuario propietario de los juegos.

    Returns:
        List[UserGame]: Lista de juegos asociados al usuario.
    """

    result = await db.execute(select(UserGame).where(UserGame.user_id == user_id))
    return result.scalars().all()


async def get_user_game(db: AsyncSession, user_id: int, game_id: int) -> Optional[UserGame]:
    """
    Obtiene un juego concreto de un usuario.

    Busca un registro en la tabla `UserGame` que pertenezca al usuario indicado
    y tenga el `game_rawg_id` especificado.

    Args:
        db (AsyncSession): Sesión asíncrona de SQLAlchemy.
        user_id (int): ID del usuario.
        game_id (int): Identificador RAWG del juego.

    Returns:
        Optional[UserGame]: Objeto `UserGame` si se encuentra, o `None` si no existe.
    """

    result = await db.execute(
        select(UserGame).where(
            UserGame.user_id == user_id,
            UserGame.game_rawg_id == game_id
        )
    )
    return result.scalar_one_or_none()


async def create_user_game(db: AsyncSession, user_id: int, data: UserGameCreate) -> UserGame:
    """
    Crea un nuevo registro de juego para un usuario.

    - Inserta una relación entre el usuario y un juego de RAWG.
    - Si faltan datos de preview (`game_title`, `image_url`, `release_year`),
      los obtiene automáticamente desde la API de RAWG.

    Args:
        db (AsyncSession): Sesión asíncrona de SQLAlchemy.
        user_id (int): ID del usuario propietario.
        data (UserGameCreate): Datos del juego proporcionados por el cliente.

    Returns:
        UserGame: Objeto `UserGame` recién creado.
    """

    payload = data.dict(exclude_unset=True)

    # Si faltan datos visuales, intenta completarlos desde RAWG
    if not all(payload.get(k) for k in ("game_title", "image_url", "release_year")):
        preview = await _fetch_rawg_preview(payload["game_rawg_id"])
        if preview:
            for k, v in preview.items():
                payload.setdefault(k, v)

    game = UserGame(**payload, user_id=user_id)
    db.add(game)
    await db.commit()
    await db.refresh(game)
    return game


async def update_user_game(db: AsyncSession, user_id: int, game_id: int, data: UserGameUpdate) -> Optional[UserGame]:
    """
    Actualiza los datos de un juego de un usuario.

    Si el juego no existe, devuelve `None`.  
    Si al actualizar faltan los datos de preview (título, imagen o año),
    se intentan completar automáticamente con la API de RAWG.

    Args:
        db (AsyncSession): Sesión asíncrona de SQLAlchemy.
        user_id (int): ID del usuario propietario.
        game_id (int): Identificador RAWG del juego.
        data (UserGameUpdate): Campos a modificar.

    Returns:
        Optional[UserGame]: Objeto `UserGame` actualizado o `None` si no existe.
    """

    game = await get_user_game(db, user_id, game_id)
    if not game:
        return None

    # Actualizar campos del modelo con los valores nuevos
    for field, value in data.dict(exclude_unset=True).items():
        setattr(game, field, value)

    # Completar información faltante si es posible
    if not all(getattr(game, k) for k in ("game_title", "image_url", "release_year")):
        preview = await _fetch_rawg_preview(game.game_rawg_id)
        if preview:
            if not game.game_title:
                game.game_title = preview["game_title"]
            if not game.image_url:
                game.image_url = preview["image_url"]
            if not game.release_year:
                game.release_year = preview["release_year"]

    await db.commit()
    await db.refresh(game)
    return game


async def delete_user_game(db: AsyncSession, user_id: int, game_id: int) -> Optional[UserGame]:
    """
    Elimina un juego del catálogo personal de un usuario.

    Si el juego no existe o no pertenece al usuario indicado, devuelve `None`.

    Args:
        db (AsyncSession): Sesión asíncrona de SQLAlchemy.
        user_id (int): ID del usuario propietario.
        game_id (int): Identificador RAWG del juego a eliminar.

    Returns:
        Optional[UserGame]: Objeto eliminado o `None` si no se encontró.
    """

    game = await get_user_game(db, user_id, game_id)
    if not game:
        return None

    await db.delete(game)
    await db.commit()
    return game
