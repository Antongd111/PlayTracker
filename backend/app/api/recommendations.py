from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
import asyncio
from math import sqrt
from collections import defaultdict

from app.core.dependencies import get_db
from app.models.user_game import UserGame
from app.schemas.game import GamePreview
from app.core.rawg import get_game_details, list_games_by_genres

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

# Pesos por estado de los juegos
STATUS_WEIGHT: Dict[str, float] = {
    "jugando": 1.0,
    "completado": 1.0,
    "por jugar": 0.3,
}
DEFAULT_STATUS_WEIGHT = 0.4

# Parámetros por defecto
K_REPRESENTATIVE_DEFAULT = 6
G_TOP_GENRES_DEFAULT = 2
PAGES_PER_GENRE_DEFAULT = 1
PAGE_SIZE = 20

# Géneros usados en cold-start (cuando el usuario no tiene juegos)
POPULAR_GENRES = ["Action", "Adventure", "Shooter", "RPG"]

# ------------------- Utilidades -------------------

def _norm_score(s: int | None) -> float:
    """Normaliza una puntuación [0,100] a [0,1]."""
    return 0.0 if s is None else max(0, min(100, s)) / 100.0

def _w(ug: UserGame) -> float:
    """Calcula el peso de un juego del usuario para decidir representatividad."""
    base = STATUS_WEIGHT.get((ug.status or "").strip().lower(), DEFAULT_STATUS_WEIGHT)
    return base * (0.5 + 0.5 * _norm_score(ug.score))

def _parse_year(v) -> int:
    """Extrae año en formato entero a partir de una fecha o string."""
    if v is None:
        return 0
    if isinstance(v, int):
        return v
    s = str(v)
    return int(s[:4]) if len(s) >= 4 and s[:4].isdigit() else 0

def _preview_from_candidate(c: Dict[str, Any]) -> GamePreview:
    """Construye un objeto GamePreview a partir de los datos de RAWG."""
    gid = int(c.get("id"))
    title = c.get("name") or c.get("title") or c.get("slug") or f"RAWG-{gid}"
    img = c.get("background_image") or c.get("imageUrl") or ""
    year = _parse_year(c.get("released") or c.get("releaseDate"))
    return GamePreview(id=gid, title=str(title), imageUrl=str(img), year=year)

def _build_genre_profile(owned_details: List[Dict[str, Any]], reps: List[UserGame]) -> Dict[str, float]:
    """
    Construye el perfil del usuario en base a géneros.
    Cada género recibe peso positivo si los juegos fueron bien puntuados y negativo si fueron mal puntuados.
    """
    status = {ug.game_rawg_id: (ug.status or "").strip().lower() for ug in reps}
    score  = {ug.game_rawg_id: ug.score for ug in reps}

    g_aff: Dict[str, float] = defaultdict(float)
    for g in owned_details:
        gid = g.get("id")
        if not gid:
            continue
        base = STATUS_WEIGHT.get(status.get(gid, ""), DEFAULT_STATUS_WEIGHT)
        signed = base * (_norm_score(score.get(gid)) - 0.5)  # afinidad firmada [-0.5, +0.5]
        if signed == 0:
            continue
        for x in g.get("genres") or []:
            name = x["name"] if isinstance(x, dict) and "name" in x else str(x)
            g_aff[name] += signed

    # Normalización L2 sobre valores absolutos para conservar señal negativa/positiva
    denom = sqrt(sum((abs(v) ** 2) for v in g_aff.values())) or 1.0
    for k in list(g_aff.keys()):
        g_aff[k] = g_aff[k] / denom
    return g_aff

def _score_simple(c: Dict[str, Any], g_aff: Dict[str, float]) -> float:
    """
    Calcula la puntuación de un candidato.
    Fórmula: 85% afinidad por géneros (firmada) + 10% metacritic + 5% refuerzo si es shooter con afinidad positiva.
    Se reduce el peso de Metacritic para evitar que dominen siempre los mismos juegos muy valorados.
    """
    genres = [x["name"] if isinstance(x, dict) and "name" in x else str(x)
              for x in (c.get("genres") or [])]
    if not genres:
        return 0.0

    match = sum(g_aff.get(g, 0.0) for g in genres) / (sqrt(len(genres)) or 1.0)
    meta = (c.get("metacritic") or 0) / 100.0

    shooter_boost = 0.0
    if g_aff.get("Shooter", 0.0) > 0.15 and any(g.lower() == "shooter" for g in genres):
        shooter_boost = 0.05

    return 0.85 * match + 0.10 * meta + shooter_boost

# ------------------- Endpoint -------------------

@router.get("/{user_id}", response_model=List[GamePreview])
async def recommend_for_user(
    user_id: int,
    top_k: int = Query(10, ge=1, le=50),
    k_representative: int = Query(K_REPRESENTATIVE_DEFAULT, ge=3, le=20),
    g_top_genres: int = Query(G_TOP_GENRES_DEFAULT, ge=1, le=2),
    pages_per_genre: int = Query(PAGES_PER_GENRE_DEFAULT, ge=1, le=1),
    db: AsyncSession = Depends(get_db),
):
    """
    Recomendador simplificado con menor influencia de Metacritic.
    Flujo:
      - Selección de juegos representativos del usuario (K).
      - Obtención de detalles de esos juegos (K llamadas RAWG).
      - Construcción de perfil por géneros con pesos positivos y negativos.
      - Obtención de candidatos por géneros dominantes (1 llamada RAWG, ordenados por rating para reducir sesgo de Metacritic).
      - Scoring y selección de top-k priorizando afinidad de géneros.
    Total de llamadas: K + 1 (o 1 si el usuario no tiene juegos).
    """

    # Paso 0. Juegos del usuario
    res = await db.execute(select(UserGame).where(UserGame.user_id == user_id))
    ugs: List[UserGame] = list(res.scalars().all())

    # Cold-start: sin juegos -> géneros populares (orden por rating para no depender de Metacritic)
    if not ugs:
        try:
            page = await list_games_by_genres(POPULAR_GENRES, page=1, page_size=PAGE_SIZE, ordering="-rating")
        except Exception:
            page = []
        return [_preview_from_candidate(c) for c in page[:top_k]]

    # Paso 1. Selección de representativos
    reps = sorted(ugs, key=_w, reverse=True)[:k_representative]
    owned = {int(x.game_rawg_id) for x in ugs}

    # Paso 2. Detalles de los representativos
    sem = asyncio.Semaphore(min(6, k_representative))
    async def get_det(gid: int) -> Dict[str, Any]:
        async with sem:
            try:
                d = await get_game_details(gid)
                return d if isinstance(d, dict) else (getattr(d, "__dict__", {}) or {})
            except Exception:
                return {"id": gid, "genres": []}

    owned_details = await asyncio.gather(*(get_det(int(ug.game_rawg_id)) for ug in reps))

    # Paso 3. Perfil de géneros
    g_aff = _build_genre_profile(owned_details, reps)
    if not g_aff:
        try:
            page = await list_games_by_genres(POPULAR_GENRES, page=1, page_size=PAGE_SIZE, ordering="-rating")
        except Exception:
            page = []
        out = [c for c in page if int(c.get("id", 0)) not in owned][:top_k]
        return [_preview_from_candidate(c) for c in out]

    # Paso 4. Candidatos por géneros dominantes (orden por rating para reducir sesgo de Metacritic)
    top_genres = [k for k, _ in sorted(g_aff.items(), key=lambda x: x[1], reverse=True)[:g_top_genres]]
    try:
        page = await list_games_by_genres(top_genres, page=1, page_size=PAGE_SIZE, ordering="-rating")
    except Exception:
        page = []

    candidates: List[Dict[str, Any]] = []
    for c in page:
        rid = c.get("id")
        if rid and int(rid) not in owned:
            candidates.append(c)

    if not candidates:
        try:
            page = await list_games_by_genres(POPULAR_GENRES, page=1, page_size=PAGE_SIZE, ordering="-rating")
        except Exception:
            page = []
        candidates = [c for c in page if int(c.get("id", 0)) not in owned]

    # Paso 5. Scoring y selección (Metacritic con peso reducido)
    candidates.sort(key=lambda c: _score_simple(c, g_aff), reverse=True)
    selected = candidates[:top_k]

    # Paso 6. Previews
    return [_preview_from_candidate(c) for c in selected]
