from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.schemas.review import ReviewUpsertIn, ReviewOut, GameReviewsResponse
from app.services import review as service
from app.models.user import User
from app.core.logger_config import get_logger

router = APIRouter(prefix="/reviews", tags=["reviews"])
logger = get_logger(__name__)


# ENDPOINTS ------------------------------------------------------------------

# Crear o actualizar una review
@router.put("/{game_id}", response_model=ReviewOut)
async def upsert_review(
    game_id: int,
    body: ReviewUpsertIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info(f"Solicitud PUT /reviews/{game_id} por usuario {current_user.id}")
    try:
        ug = await service.upsert_review(
            db=db,
            user_id=current_user.id,
            game_id=game_id,
            score=body.score,
            notes=body.notes,
            contains_spoilers=bool(body.contains_spoilers),
        )

        logger.info(f"Reseña actualizada o creada correctamente (user={current_user.id}, game={game_id})")
        return ReviewOut(
            user_id=ug.user_id,
            game_id=ug.game_id,
            score=ug.score,
            notes=ug.notes,
            contains_spoilers=bool(ug.contains_spoilers),
            review_updated_at=ug.review_updated_at.isoformat() if ug.review_updated_at else None,
            username=current_user.username,
            avatar_url=current_user.avatar_url,
            likes_count=0,
            liked_by_me=False,
        )
    except Exception as e:
        logger.exception(f"Error al crear/actualizar reseña (user={current_user.id}, game={game_id}): {e}")
        raise HTTPException(status_code=500, detail="Error interno al actualizar reseña")


# Obtener todas las reviews de un juego
@router.get("/game/{game_id}", response_model=GameReviewsResponse)
async def list_reviews_for_game(
    game_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info(f"Solicitud GET /reviews/game/{game_id} (limit={limit}) por usuario {current_user.id}")
    try:
        avg, cnt = await service.get_game_reviews_stats(db, game_id)
        rows = await service.list_reviews_for_game(
            db, game_id, viewer_user_id=current_user.id, limit=limit
        )

        logger.info(f"Devueltas {len(rows)} reseñas (game={game_id}, avg={avg}, count={cnt})")
        return GameReviewsResponse(
            game_id=game_id,
            avg_score_global=avg,
            count_reviews=cnt,
            reviews=[
                ReviewOut(
                    user_id=r["user_id"],
                    game_id=r["game_id"],
                    score=r["score"],
                    notes=r["notes"],
                    contains_spoilers=bool(r["contains_spoilers"]),
                    review_updated_at=r["review_updated_at"].isoformat() if r["review_updated_at"] else None,
                    username=r["username"],
                    avatar_url=r["avatar_url"],
                    likes_count=int(r["likes_count"] or 0),
                    liked_by_me=bool(r["liked_by_me"]),
                )
                for r in rows
            ],
        )
    except Exception as e:
        logger.exception(f"Error al obtener reseñas del juego {game_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno al listar reseñas")


# Dar like a una reseña
@router.post("/{game_id}/{author_user_id}/like")
async def like_review(
    game_id: int,
    author_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info(f"Solicitud POST /reviews/{game_id}/{author_user_id}/like por usuario {current_user.id}")
    try:
        ok = await service.like_review(
            db, liker_user_id=current_user.id, author_user_id=author_user_id, game_id=game_id
        )
        if not ok:
            logger.warning(f"Like fallido: reseña no encontrada (game={game_id}, author={author_user_id})")
            raise HTTPException(status_code=404, detail="Review not found")
        logger.info(f"Like registrado correctamente (user={current_user.id} → author={author_user_id}, game={game_id})")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error al dar like (user={current_user.id}, game={game_id}): {e}")
        raise HTTPException(status_code=500, detail="Error interno al registrar like")


# Quitar like de una reseña
@router.delete("/{game_id}/{author_user_id}/like")
async def unlike_review(
    game_id: int,
    author_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info(f"Solicitud DELETE /reviews/{game_id}/{author_user_id}/like por usuario {current_user.id}")
    try:
        await service.unlike_review(
            db, liker_user_id=current_user.id, author_user_id=author_user_id, game_id=game_id
        )
        logger.info(f"Like eliminado correctamente (user={current_user.id} → author={author_user_id}, game={game_id})")
        return {"ok": True}
    except Exception as e:
        logger.exception(f"Error al eliminar like (user={current_user.id}, game={game_id}): {e}")
        raise HTTPException(status_code=500, detail="Error interno al eliminar like")
