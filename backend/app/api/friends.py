from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.dependencies import get_db, get_current_user
from app.schemas.friendship import FriendOut, FriendshipRequestOut, UserLite
from app.crud import friendship as crud_friendship

router = APIRouter(prefix="/friends", tags=["friends"])

@router.post("/requests/{to_user_id}", status_code=201)
async def send_request(
    to_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    ok = await crud_friendship.send_request(db, current_user.id, to_user_id)
    if not ok:
        # ya existe relación o no se puede reabrir
        raise HTTPException(status_code=400, detail="No se pudo crear la solicitud")
    return {"ok": True}

@router.post("/{from_user_id}/accept")
async def accept_request(
    from_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    ok = await crud_friendship.accept_request(db, current_user.id, from_user_id)
    if not ok:
        raise HTTPException(status_code=400, detail="No hay solicitud pendiente de ese usuario")
    return {"ok": True}

@router.post("/{from_user_id}/decline")
async def decline_request(
    from_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    ok = await crud_friendship.decline_request(db, current_user.id, from_user_id)
    if not ok:
        raise HTTPException(status_code=400, detail="No hay solicitud pendiente de ese usuario")
    return {"ok": True}

@router.delete("/{other_user_id}")
async def unfriend(
    other_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    ok = await crud_friendship.unfriend(db, current_user.id, other_user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="No hay amistad que eliminar")
    return {"ok": True}



@router.delete("/requests/{to_user_id}")
async def cancel_request(
    to_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    ok = await crud_friendship.cancel_request(db, current_user.id, to_user_id)
    if not ok:
        # idempotente: si no hay nada que cancelar devolvemos 404 o 200 con ok=false; 
        # siguiendo tu estilo, mejor 400/404 consistente:
        raise HTTPException(status_code=404, detail="No hay solicitud pendiente que cancelar")
    return {"ok": True}

@router.post("/{other_user_id}/block")
async def block_user(
    other_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    await crud_friendship.block_user(db, current_user.id, other_user_id)
    return {"ok": True}

@router.get("", response_model=List[FriendOut])
async def list_friends(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    rows = await crud_friendship.list_friends(db, current_user.id)
    return [FriendOut(id=u.id, username=u.username, avatar_url=u.avatar_url) for u in rows]

@router.get("/of/{user_id}", response_model=List[FriendOut])
async def list_friends_of(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_user),
):
    rows = await crud_friendship.list_friends(db, user_id)
    # rows son objetos User
    return [FriendOut(id=u.id, username=u.username, avatar_url=u.avatar_url) for u in rows]

@router.get("/requests/incoming", response_model=List[FriendshipRequestOut])
async def incoming_requests(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    rows = await crud_friendship.list_incoming_requests(db, current_user.id)
    return [
        FriendshipRequestOut(
            requester_id=r["requester_id"],
            other_user=UserLite(id=r["other_id"], username=r["username"], avatar_url=r["avatar_url"]),
            status=r["status"],
            requested_at=r["requested_at"],
        )
        for r in rows
    ]

@router.get("/requests/outgoing", response_model=List[FriendshipRequestOut])
async def outgoing_requests(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    rows = await crud_friendship.list_outgoing_requests(db, current_user.id)
    return [
        FriendshipRequestOut(
            requester_id=r["requester_id"],
            other_user=UserLite(id=r["other_id"], username=r["username"], avatar_url=r["avatar_url"]),
            status=r["status"],
            requested_at=r["requested_at"],
        )
        for r in rows
    ]
