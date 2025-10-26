import httpx
from fastapi import HTTPException
from typing import List, Dict, Any, Optional
from app.core.config import settings

RAWG_API_BASE_URL = "https://api.rawg.io/api"

# =========================
# Helpers internos
# =========================

async def _rawg_get(path: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
    """
    Helper para GET a RAWG con timeout y API key.
    NO transforma el payload; devuelve el Response para que el caller decida.
    """
    merged = {"key": settings.RAWG_API_KEY}
    if params:
        merged.update(params)

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(f"{RAWG_API_BASE_URL}{path}", params=merged)
    return resp


# =========================
# Mapeadores de salida
# =========================

# Función para mapear los datos al formato del frontend (reducido)
def format_game(game: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": game["id"],
        "title": game["name"],
        "year": int(game["released"][:4]) if game.get("released") else 0,
        "imageUrl": game.get("background_image", ""),
        "rating": game.get("rating", 0)
    }

# Función para mapear los datos al formato del frontend
def format_game_detail(
    game: Dict[str, Any],
    screenshots: Dict[str, Any],
    trailers: Dict[str, Any],
    similar_games: Dict[str, Any]
) -> Dict[str, Any]:
    return {
        "id": game["id"],
        "title": game["name"],
        "description": game.get("description_raw", ""),
        "releaseDate": game.get("released"),
        "imageUrl": game.get("background_image", ""),
        "rating": game.get("rating", 0),
        "platforms": [p["platform"]["name"] for p in game.get("platforms", [])],
        "genres": [g["name"] for g in game.get("genres", [])],
        "developers": [d["name"] for d in game.get("developers", [])],
        "publishers": [p["name"] for p in game.get("publishers", [])],
        "tags": [t["name"] for t in game.get("tags", [])],
        "esrbRating": game["esrb_rating"]["name"] if game.get("esrb_rating") else None,
        "metacriticScore": game.get("metacritic"),
        "metacriticUrl": game.get("metacritic_url"),
        "website": game.get("website"),
        "screenshots": [s["image"] for s in screenshots.get("results", [])],
        "videos": [v["data"]["480"] for v in trailers.get("results", []) if "data" in v and "480" in v["data"]],
        "similarGames": [
            {"id": g["id"], "title": g["name"], "imageUrl": g.get("background_image", "")}
            for g in similar_games.get("results", [])
        ]
    }


# =========================
# Búsquedas y detalle
# =========================

# Buscar juegos por nombre
async def search_games(query: str) -> List[Dict[str, Any]]:
    params = {
        "search": query,
        "page_size": 10
    }
    response = await _rawg_get("/games", params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error al conectar con RAWG API")

    data = response.json()
    return [format_game(game) for game in data.get("results", [])]

# Obtener detalles de un juego por ID
async def get_game_from_rawg(game_id: int) -> Dict[str, Any]:
    # Juego principal
    response = await _rawg_get(f"/games/{game_id}")
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="No se pudo obtener el detalle del juego")
    game = response.json()

    # Screenshots
    screenshots_resp = await _rawg_get(f"/games/{game_id}/screenshots")
    screenshots = screenshots_resp.json() if screenshots_resp.status_code == 200 else {"results": []}

    # Trailers
    trailers_resp = await _rawg_get(f"/games/{game_id}/movies")
    trailers = trailers_resp.json() if trailers_resp.status_code == 200 else {"results": []}

    # Juegos similares
    similar_resp = await _rawg_get(f"/games/{game_id}/suggested")
    similar_games = similar_resp.json() if similar_resp.status_code == 200 else {"results": []}

    return format_game_detail(game, screenshots, trailers, similar_games)


# Obtener juegos populares
async def get_popular_games(page: int = 1, size: int = 10) -> List[Dict[str, Any]]:
    params = {
        # Los más añadidos por usuarios → suelen ser conocidos
        "ordering": "-added",
        # Rango de fechas: del 1 de enero 2024 hasta hoy
        "dates": "2025-01-01,2025-12-31",
        "page_size": size,
        "page": page
    }
    response = await _rawg_get("/games", params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="No se pudieron obtener juegos populares")

    data = response.json()
    return [format_game(game) for game in data.get("results", [])]

# Obtener lista de géneros
async def get_genres() -> Dict[str, Any]:
    response = await _rawg_get("/genres")
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="No se pudieron obtener los géneros")
    return response.json()


# =========================
# Listar juegos por géneros
# =========================

async def list_games_by_genres(
    genres: List[str],
    page: int = 1,
    page_size: int = 40,
    ordering: str = "-metacritic",
) -> List[Dict[str, Any]]:
    """
    Devuelve una lista de juegos (dicts crudos de RAWG) filtrados por varios géneros a la vez.
    Se usa para obtener candidatos en pocas llamadas desde el recomendador.
    No aplica formateo: el recomendador usa campos como:
      - id, name, background_image, released, metacritic
      - genres (lista de {name}), tags (si el endpoint los incluye), developers (si los incluye)
    """
    # RAWG espera nombres de géneros en minúsculas y separados por comas.
    genre_param = ",".join(g.strip().lower() for g in genres if g and g.strip())
    params = {
        "genres": genre_param,
        "page": page,
        "page_size": page_size,
        "ordering": ordering,
    }

    response = await _rawg_get("/games", params=params)
    if response.status_code != 200:
        return []

    data = response.json() or {}
    results = data.get("results", []) or []
    return results
