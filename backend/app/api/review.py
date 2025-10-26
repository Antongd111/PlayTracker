from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.schemas.review import ReviewUpsertIn, ReviewOut, GameReviewsResponse
from app.services import review as service
from app.models.user import User

router = APIRouter(prefix="/reviews", tags=["reviews"])

# ENDPOINTS ------------------------------------------------------------------

# Actualizar review
@router.put("/{game_id}", response_model=ReviewOut)
async def upsert_review(
    game_id: int,
    body: ReviewUpsertIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ug = await service.upsert_review(
        db=db,
        user_id=current_user.id,
        game_id=game_id,
        score=body.score,
        notes=body.notes,
        contains_spoilers=bool(body.contains_spoilers),
    )

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

# Obtener reviews de un juego
@router.get("/game/{game_id}", response_model=GameReviewsResponse)
async def list_reviews_for_game(
    game_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    avg, cnt = await service.get_game_reviews_stats(db, game_id)
    rows = await service.list_reviews_for_game(
        db, game_id, viewer_user_id=current_user.id, limit=limit
    )

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
            ) for r in rows
        ],
    )

# Dar Like a una review
@router.post("/{game_id}/{author_user_id}/like")
async def like_review(
    game_id: int,
    author_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ok = await service.like_review(
        db, liker_user_id=current_user.id, author_user_id=author_user_id, game_id=game_id
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"ok": True}

# Borrar Like de una review
@router.delete("/{game_id}/{author_user_id}/like")
async def unlike_review(
    game_id: int,
    author_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await service.unlike_review(
        db, liker_user_id=current_user.id, author_user_id=author_user_id, game_id=game_id
    )
    return {"ok": True}
