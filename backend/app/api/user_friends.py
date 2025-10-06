from fastapi import APIRouter, Depends, Query
from typing import List
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services import friendship as service

users_friends_router = APIRouter(prefix="/users/{user_id}", tags=["users"])

# ENDPOINTS ------------------------------------------------------------------

# Listar amigos de un usuario
@users_friends_router.get("/friends")
async def list_user_friends(user_id: int, db = Depends(get_db), _ = Depends(get_current_user)):
    rows = await service.list_friends(db, user_id)
    return [{"id": u.id, "username": u.username, "avatar_url": u.avatar_url} for u in rows]

# Listar solicitudes de amistad (incoming | outgoing)
@users_friends_router.get("/friend-requests")
async def list_user_requests(
    user_id: int,
    direction: str = Query("incoming", regex="^(incoming|outgoing)$"),
    db = Depends(get_db),
    _ = Depends(get_current_user),
):
    if direction == "incoming":
        rows = await service.list_incoming_requests(db, user_id)
    else:
        rows = await service.list_outgoing_requests(db, user_id)
    return rows