from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.services import friendship as service
from app.core.logger_config import get_logger

users_friends_router = APIRouter(prefix="/users/{user_id}", tags=["users"])
logger = get_logger(__name__)

# ENDPOINTS ------------------------------------------------------------------

# Listar amigos de un usuario
@users_friends_router.get("/friends")
async def list_user_friends(user_id: int, db=Depends(get_db), _=Depends(get_current_user)):
    logger.info(f"Solicitud GET /users/{user_id}/friends (listar amigos)")
    try:
        rows = await service.list_friends(db, user_id)
        logger.info(f"Usuario {user_id} tiene {len(rows)} amigos.")
        return [{"id": u.id, "username": u.username, "avatar_url": u.avatar_url} for u in rows]
    except Exception as e:
        logger.exception(f"Error al listar amigos del usuario {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno al listar amigos")


# Listar solicitudes de amistad (incoming | outgoing)
@users_friends_router.get("/friend-requests")
async def list_user_requests(
    user_id: int,
    direction: str = Query("incoming", pattern="^(incoming|outgoing)$"),
    db=Depends(get_db),
    _=Depends(get_current_user),
):
    logger.info(f"Solicitud GET /users/{user_id}/friend-requests?direction={direction}")
    try:
        if direction == "incoming":
            rows = await service.list_incoming_requests(db, user_id)
            logger.info(f"Usuario {user_id} tiene {len(rows)} solicitudes de amistad entrantes.")
        else:
            rows = await service.list_outgoing_requests(db, user_id)
            logger.info(f"Usuario {user_id} tiene {len(rows)} solicitudes de amistad salientes.")
        return rows
    except Exception as e:
        logger.exception(f"Error al listar solicitudes de amistad de {user_id} ({direction}): {e}")
        raise HTTPException(status_code=500, detail="Error interno al listar solicitudes de amistad")
