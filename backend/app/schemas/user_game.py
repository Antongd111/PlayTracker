# app/schemas/user_game.py
from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# ---------- Base para creación ----------
class UserGameCreate(BaseModel):
    """
    Body para crear un UserGame. Solo requiere el RAWG ID del juego.
    """
    game_rawg_id: int = Field(..., alias="gameRawgId")
    status: Optional[str] = None
    score: Optional[int] = None
    notes: Optional[str] = None
    contains_spoilers: Optional[bool] = Field(False, alias="containsSpoilers")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra='ignore',       # ignora cualquier campo extra que mande el cliente
        str_strip_whitespace=True,
    )

# ---------- Base para actualización ----------
class UserGameUpdate(BaseModel):
    """
    Body para actualizar SOLO campos del usuario.
    """
    status: Optional[str] = None
    score: Optional[int] = None
    notes: Optional[str] = None
    contains_spoilers: Optional[bool] = Field(None, alias="containsSpoilers")

    model_config = ConfigDict(
        populate_by_name=True,
        extra='ignore',
        str_strip_whitespace=True,
    )

# ---------- Salida ----------
class UserGameOut(BaseModel):
    """
    DTO de salida. Incluye previews del juego obtenidos de la tabla `games`.
    """
    id: int
    user_id: int = Field(..., alias="userId")
    game_rawg_id: int = Field(..., alias="gameRawgId")

    # previews (derivados de `games`, NO se envían en create/update)
    game_title: Optional[str] = Field(None, alias="gameTitle")
    image_url: Optional[str] = Field(None, alias="imageUrl")
    release_year: Optional[int] = Field(None, alias="releaseYear")

    # campos del usuario
    status: Optional[str] = None
    score: Optional[int] = None
    notes: Optional[str] = None
    added_at: datetime = Field(..., alias="addedAt")
    review_updated_at: Optional[datetime] = Field(None, alias="reviewUpdatedAt")
    contains_spoilers: Optional[bool] = Field(None, alias="containsSpoilers")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )
