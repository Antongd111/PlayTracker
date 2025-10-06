from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import SessionLocal
from app.schemas.user import UserOut, UserCreate, UserUpdate
from app.services import user as service
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])

# Helpers --------------------------------------------------------------------

async def get_db():
    async with SessionLocal() as session:
        yield session

async def get_user_or_404(user_id: int, db: AsyncSession) -> User:
    user = await service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


# ENDPOINTS ------------------------------------------------------------------

# Listado
@router.get("/", response_model=List[UserOut])
async def read_users(db: AsyncSession = Depends(get_db), q: Optional[str] = None):
    if q:
        return await service.search_users(db, q)
    return await service.get_users(db)

# Obtener el usuario asociado al token
@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# Obtener un usuario por Id
@router.get("/{user_id}", response_model=UserOut)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    return await get_user_or_404(user_id, db)

# Crear un usuario
@router.post("/", response_model=UserOut, status_code=201)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_user(db, user)

# Modificar un usuario
@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    user_update: UserUpdate,  # asegúrate de que los campos sean Optional[...] en el schema
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    await get_user_or_404(user_id, db)
    updated = await service.update_user(db, user_id, user_update)
    return updated

# Borrar un usuario
@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    await get_user_or_404(user_id, db)
    await service.delete_user(db, user_id)


# # Obtener usuarios relacionados con una búsqueda
# @router.get("/search/", response_model=List[UserOut])
# async def search_users(query: str, db: AsyncSession = Depends(get_db)):
#     users = await service.search_users(db, query)
#     return users

# # Cambiar el juego favorito de un usuario
# @router.patch("/{user_id}/favorite", response_model=UserOut)
# async def set_favorite_for_user(
#     user_id: int,
#     body: FavoriteUpdate,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     # Solo se puede cambiar el juego favorito de uno mismo
#     if current_user.id != user_id:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

#     updated = await service.set_favorite(
#         db=db,
#         user_id=user_id,
#         favorite_rawg_game_id=body.favorite_rawg_game_id,
#     )
#     if not updated:
#         raise HTTPException(status_code=404, detail="Usuario no encontrado")
#     return updated

# # Obtener la lista de juegos de los amigos de un usuario
# @router.get("/{user_id}/friends/games", response_model=List[GamePreview])
# async def friends_games_endpoint(
#     user_id: int,
#     db: AsyncSession = Depends(get_db),
# ):
#     return await get_friends_games(db, user_id=user_id, limit=10)