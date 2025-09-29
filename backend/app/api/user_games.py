from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import SessionLocal
from app.schemas.user_game import *
from app.crud import user_game as crud

router = APIRouter(prefix="/users/{user_id}/games", tags=["user_games"])

async def get_db():
    async with SessionLocal() as session:
        yield session

# Obtener UserGame
@router.get("/{game_id}", response_model=UserGameOut)
async def get_game(user_id: int, game_id: int, db: AsyncSession = Depends(get_db)):
    game = await crud.get_user_game(db, user_id, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Juego no encontrado")
    return game

@router.get("/", response_model=List[UserGameOut])
async def list_games(user_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.get_user_games(db, user_id)

@router.post("/", response_model=UserGameOut, status_code=201)
async def add_game(user_id: int, data: UserGameCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_user_game(db, user_id, data)

@router.put("/{game_id}", response_model=UserGameOut)
async def update_game(user_id: int, game_id: int, data: UserGameUpdate, db: AsyncSession = Depends(get_db)):
    updated = await crud.update_user_game(db, user_id, game_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Juego no encontrado")
    return updated

@router.delete("/{game_id}", status_code=204)
async def delete_game(user_id: int, game_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await crud.delete_user_game(db, user_id, game_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Juego no encontrado")