from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services import friendship as service

router = APIRouter(prefix="/friendships", tags=["friendships"])

# Crear solicitud (from = current_user, to = body.to_user_id o query)
@router.post("", status_code=201)
async def create_friendship(
    to_user_id: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
    me: User = Depends(get_current_user),
):
    ok = await service.send_request(db, me.id, to_user_id)
    if not ok:
        raise HTTPException(status_code=400, detail="No se pudo crear la solicitud")
    return {"ok": True}

# Listar relaciones (de un usuario y/o por estado)
@router.get("")
async def list_friendships(
    user_id: Optional[int] = None,
    status_filter: Optional[str] = Query(None, regex="^(pending|accepted|declined|blocked)$"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    # Puedes crear un método unificado en services; aquí reusamos los tuyos
    if status_filter == "pending":
        if user_id is None:
            raise HTTPException(status_code=400, detail="user_id requerido para pending")
        incoming = await service.list_incoming_requests(db, user_id)
        outgoing = await service.list_outgoing_requests(db, user_id)
        return {"incoming": incoming, "outgoing": outgoing}
    elif status_filter == "accepted":
        uid = user_id or _.id
        rows = await service.list_friends(db, uid)
        return [{"id": u.id, "username": u.username, "avatar_url": u.avatar_url} for u in rows]
    else:
        # otras vistas opcionales
        return {"ok": True}

# Transición de estado: accept | decline | block
@router.patch("/{friendship_id}")
async def update_friendship_status(
    friendship_id: int,
    action: str = Query(..., regex="^(accept|decline|block)$"),
    db: AsyncSession = Depends(get_db),
    me: User = Depends(get_current_user),
):
    if action == "accept":
        ok = await service.accept_request(db, me.id, from_user_id=None, friendship_id=friendship_id)
    elif action == "decline":
        ok = await service.decline_request(db, me.id, from_user_id=None, friendship_id=friendship_id)
    else:
        ok = await service.block_user(db, me.id, other_user_id=None, friendship_id=friendship_id)
    if not ok:
        raise HTTPException(status_code=400, detail="No se pudo actualizar")
    return {"ok": True}

# Eliminar amistad (unfriend)
@router.delete("/{friendship_id}", status_code=204)
async def delete_friendship(
    friendship_id: int,
    db: AsyncSession = Depends(get_db),
    me: User = Depends(get_current_user),
):
    ok = await service.unfriend(db, me.id, other_user_id=None, friendship_id=friendship_id)
    if not ok:
        raise HTTPException(status_code=404, detail="No existe la amistad")
