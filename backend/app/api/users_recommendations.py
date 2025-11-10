from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.dependencies import get_db
from app.schemas.game import GamePreview

router = APIRouter(prefix="/users/{user_id}/recommendations", tags=["users", "recommendations"])

# ENDPOINTS ------------------------------------------------------------------

# Obtener recomendaciones de juegos para un usuario (por implementar)
@router.get("", response_model=List[GamePreview])
async def user_recommendations(
    user_id: int,
    top_k: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    return []
