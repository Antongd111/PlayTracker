from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import SessionLocal
from app.schemas.user import UserOut, UserCreate, UserUpdate, FavoriteUpdate
from app.crud import user as crud_user
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.game import GamePreview
from app.crud.user import get_friends_games

router = APIRouter(prefix="/users", tags=["users"])

async def get_db():
    async with SessionLocal() as session:
        yield session

# Obtener usuario
@router.get("/", response_model=List[UserOut])
async def read_users(db: AsyncSession = Depends(get_db)):
    return await crud_user.get_users(db)

# Obtener la lista de juegos de los amigos de un usuario
@router.get("/{user_id}/friends/games", response_model=List[GamePreview])
async def friends_games_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await get_friends_games(db, user_id=user_id, limit=10)

# Obtener el usuario asociado al token
@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# Obtener un usuario por Id
@router.get("/{user_id}", response_model=UserOut)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await crud_user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

# Crear un usuario
@router.post("/", response_model=UserOut, status_code=201)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    return await crud_user.create_user(db, user)

# Modificar un usuario
@router.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, user_update: UserUpdate, db: AsyncSession = Depends(get_db)):
    updated = await crud_user.update_user(db, user_id, user_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return updated

# Borrar un usuario
@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await crud_user.delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

# Obtener usuarios relacionados con una búsqueda
@router.get("/search/", response_model=List[UserOut])
async def search_users(query: str, db: AsyncSession = Depends(get_db)):
    users = await crud_user.search_users(db, query)
    return users

# Cambiar el juego favorito de un usuario
@router.patch("/{user_id}/favorite", response_model=UserOut)
async def set_favorite_for_user(
    user_id: int,
    body: FavoriteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Solo se puede cambiar el juego favorito de uno mismo
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    updated = await crud_user.set_favorite(
        db=db,
        user_id=user_id,
        favorite_rawg_game_id=body.favorite_rawg_game_id,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return updated