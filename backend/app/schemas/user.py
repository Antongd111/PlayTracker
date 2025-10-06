from pydantic import BaseModel, EmailStr
from typing import Optional

# -------- Base / Create / Out --------

class UserBase(BaseModel):
    email: EmailStr
    username: str
    status: Optional[str] = "Disponible"
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    favorite_rawg_game_id: Optional[int] = None

    class Config:
        orm_mode = True
        anystr_strip_whitespace = True
        extra = "forbid"   # No aceptar campos desconocidos

# -------- Update (parcial) --------

class UserUpdate(BaseModel):
    username: Optional[str] = None
    status: Optional[str] = None
    avatar_url: Optional[str] = None
    favorite_rawg_game_id: Optional[int] = None

    class Config:
        extra = "forbid"   # No aceptar cambios desconocidos en el patch
        anystr_strip_whitespace = True