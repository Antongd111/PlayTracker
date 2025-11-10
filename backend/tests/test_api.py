import pytest
from fastapi.testclient import TestClient
from app import *
from fastapi import HTTPException
import app.api.games as game

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

# ----------------------------------------------------------------------
# ENDPOINTS DE games
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_games(client):
    query = "Halo"
    
    # Realizar la solicitud a la API
    response = client.get(f"/games/search?query={query}")
    
    # Comprobaciones
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0
    assert response.json()[0]["title"] == "Halo"


@pytest.mark.asyncio
async def test_get_popular_games(client):
    page = 1
    
    # Realizar la solicitud a la API
    response = client.get(f"/games/popular?page={page}")
    
    # Comprobaciones
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0
    assert "title" in response.json()[0]

@pytest.mark.asyncio
async def test_get_genres(client):
    # Realizar la solicitud a la API
    response = client.get("/games/genres")
    
    # Comprobaciones
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert "results" in response.json()
    assert len(response.json()["results"]) > 0


@pytest.mark.asyncio
async def test_get_game_details(client):
    game_id = 1
    
    # Realizar la solicitud a la API
    response = client.get(f"/games/{game_id}")
    
    # Comprobaciones
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["id"] == game_id

@pytest.mark.asyncio
async def test_get_game_not_found(client):
    game_id = 9999
    
    # Realizar la solicitud a la API
    response = client.get(f"/games/{game_id}")
    
    # Comprobaciones
    assert response.status_code == 404
    assert response.json() == {"detail": "Game not found"}

@pytest.mark.asyncio
async def test_get_game_details_server_error(client, monkeypatch):
    async def mock_get_game_from_rawg(game_id: int):
        raise HTTPException(status_code=500, detail="Cache/DB error")

    monkeypatch.setattr(game, "get_game_from_rawg", mock_get_game_from_rawg)

    game_id = 1
    
    # Realizar la solicitud a la API
    response = client.get(f"/games/{game_id}")
    
    # Comprobaciones
    assert response.status_code == 500
    assert response.json() == {"detail": "Cache/DB error"}
