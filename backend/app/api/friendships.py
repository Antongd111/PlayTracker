from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services import friendship as service
from app.core.logger_config import get_logger

from sqlalchemy import select, or_, and_
from app.models.friendship import Friendship

router = APIRouter(prefix="/friendships", tags=["friendships"])
logger = get_logger(__name__)


# ENDPOINTS ------------------------------------------------------------------

# Crear solicitud de amistad
@router.post("", status_code=201)
async def create_friendship(
    to_user_id: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
    me: User = Depends(get_current_user),
):
    logger.info(f"Solicitud POST /friendships: {me.id} → {to_user_id}")
    try:
        ok = await service.send_request(db, me.id, to_user_id)
        if not ok:
            logger.warning(f"No se pudo crear la solicitud de amistad ({me.id} → {to_user_id})")
            raise HTTPException(status_code=400, detail="No se pudo crear la solicitud")
        logger.info(f"Solicitud de amistad enviada correctamente ({me.id} → {to_user_id})")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error al crear la solicitud de amistad ({me.id} → {to_user_id}): {e}")
        raise HTTPException(status_code=500, detail="Error interno al crear la solicitud")


# Listar relaciones (de un usuario y/o por estado)
@router.get("")
async def list_friendships(
    user_id: Optional[int] = None,
    status_filter: Optional[str] = Query(None, regex="^(pending|accepted|declined|blocked)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info(f"Solicitud GET /friendships (user_id={user_id}, status={status_filter}) por usuario {current_user.id}")
    try:
        # CASO 1: SOLICITUDES PENDIENTES (Entrantes y Salientes)
        if status_filter == "pending":
            if user_id is None:
                logger.warning(f"Falta user_id para filtrar pending (usuario {current_user.id})")
                raise HTTPException(status_code=400, detail="user_id requerido para pending")
            
            # Obtenemos las filas planas del servicio
            incoming_rows = await service.list_incoming_requests(db, user_id)
            outgoing_rows = await service.list_outgoing_requests(db, user_id)

            # Formateador para anidar el 'other_user' como espera el frontend (IncomingReqDto)
            def format_request(row):
                return {
                    "friendship_id": row["friendship_id"],
                    "requester_id": row["requester_id"],
                    "status": row["status"],
                    "requested_at": row["requested_at"].isoformat() if row["requested_at"] else None,
                    "other_user": {
                        "id": row["other_id"],
                        "username": row["username"],
                        "avatar_url": row["avatar_url"]
                    }
                }

            logger.info(f"Usuario {user_id} tiene {len(incoming_rows)} solicitudes entrantes y {len(outgoing_rows)} salientes")
            return {
                "incoming": [format_request(r) for r in incoming_rows],
                "outgoing": [format_request(r) for r in outgoing_rows]
            }

        # CASO 2: AMIGOS ACEPTADOS
        elif status_filter == "accepted":
            uid = user_id or current_user.id
            
            # Consultamos el Usuario y el ID de la relación para que el frontend pueda borrar amigos
            q = (
                select(User, Friendship.id.label("f_id"))
                .join(Friendship, or_(
                    and_(Friendship.user_id_a == uid, User.id == Friendship.user_id_b),
                    and_(Friendship.user_id_b == uid, User.id == Friendship.user_id_a)
                ))
                .where(Friendship.status == "accepted")
            )
            res = await db.execute(q)
            rows = res.all()
            
            logger.info(f"Usuario {uid} tiene {len(rows)} amigos aceptados")
            return [
                {
                    "id": u.id, 
                    "username": u.username, 
                    "avatar_url": u.avatar_url,
                    "friendship_id": f_id # Crucial para FriendDto en el frontend
                } for u, f_id in rows
            ]

        # CASO 3: CONSULTA GENÉRICA
        else:
            logger.info(f"Consulta genérica de friendships (sin filtro) para user_id={user_id}")
            return {"ok": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error al listar friendships (user_id={user_id}, status={status_filter}): {e}")
        raise HTTPException(status_code=500, detail="Error interno al listar amistades")


# Transición de estado: accept | decline | block
@router.patch("/{friendship_id}")
async def update_friendship_status(
    friendship_id: int,
    action: str = Query(..., regex="^(accept|decline|block)$"),
    db: AsyncSession = Depends(get_db),
    me: User = Depends(get_current_user),
):
    logger.info(f"Solicitud PATCH /friendships/{friendship_id}?action={action} por usuario {me.id}")
    try:
        if action == "accept":
            ok = await service.accept_request(db, me.id, from_user_id=None, friendship_id=friendship_id)
        elif action == "decline":
            ok = await service.decline_request(db, me.id, from_user_id=None, friendship_id=friendship_id)
        else:
            ok = await service.block_user(db, me.id, other_user_id=None, friendship_id=friendship_id)

        if not ok:
            logger.warning(f"No se pudo actualizar amistad {friendship_id} (acción={action}) por {me.id}")
            raise HTTPException(status_code=400, detail="No se pudo actualizar")

        logger.info(f"Acción '{action}' aplicada correctamente sobre amistad {friendship_id} por usuario {me.id}")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error al actualizar amistad {friendship_id} (acción={action}, user={me.id}): {e}")
        raise HTTPException(status_code=500, detail="Error interno al actualizar amistad")


# Eliminar amistad (unfriend)
@router.delete("/{friendship_id}", status_code=204)
async def delete_friendship(
    friendship_id: int,
    db: AsyncSession = Depends(get_db),
    me: User = Depends(get_current_user),
):
    logger.info(f"Solicitud DELETE /friendships/{friendship_id} por usuario {me.id}")
    try:
        ok = await service.unfriend(db, me.id, other_user_id=None, friendship_id=friendship_id)
        if not ok:
            logger.warning(f"No existe la amistad {friendship_id} para usuario {me.id}")
            raise HTTPException(status_code=404, detail="No existe la amistad")
        logger.info(f"Amistad {friendship_id} eliminada correctamente por usuario {me.id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error al eliminar amistad {friendship_id} (user={me.id}): {e}")
        raise HTTPException(status_code=500, detail="Error interno al eliminar amistad")
