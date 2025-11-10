import pytest
from fastapi.testclient import TestClient
from main import app
from fastapi import HTTPException
import app.api.games as game
from httpx import AsyncClient

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def user_data():
    return {
        "email": "testuser@example.com",
        "username": "testuser",
        "hashed_password": "fakepassword",
        "status": "active",
    }


@pytest.fixture
def user_update_data():
    return {
        "email": "updateduser@example.com",
        "username": "updateduser",
    }
# ----------------------------------------------------------------------
# ENDPOINTS DE games
# ----------------------------------------------------------------------

# @pytest.mark.asyncio
# async def test_search_games(client):
#     query = "Halo"
    
#     # Realizar la solicitud a la API
#     response = client.get(f"/rawg/games/search?query={query}")
    
#     # Comprobaciones
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)
#     assert len(response.json()) > 0
#     assert response.json()[0]["title"] == "Halo"


# @pytest.mark.asyncio
# async def test_get_popular_games(client):
#     page = 1
    
#     # Realizar la solicitud a la API
#     response = client.get(f"/rawg/games/popular?page={page}")
    
#     # Comprobaciones
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)
#     assert len(response.json()) > 0
#     assert "title" in response.json()[0]

# @pytest.mark.asyncio
# async def test_get_genres(client):
#     # Realizar la solicitud a la API
#     response = client.get("/rawg/games/genres")
    
#     # Comprobaciones
#     assert response.status_code == 200
#     assert isinstance(response.json(), dict)
#     assert "results" in response.json()
#     assert len(response.json()["results"]) > 0


# @pytest.mark.asyncio
# async def test_get_game_details(client):
#     game_id = 1
    
#     # Realizar la solicitud a la API
#     response = client.get(f"/rawg/games/{game_id}")
    
#     # Comprobaciones
#     assert response.status_code == 200
#     assert "id" in response.json()
#     assert response.json()["id"] == game_id

# @pytest.mark.asyncio
# async def test_get_game_not_found(client):
#     game_id = 9999
    
#     # Realizar la solicitud a la API
#     response = client.get(f"/rawg/games/{game_id}")
    
#     # Comprobaciones
#     assert response.status_code == 404
#     assert response.json() == {"detail": "Game not found"}

# @pytest.mark.asyncio
# async def test_get_game_details_server_error(client, monkeypatch):
#     async def mock_get_game_from_rawg(game_id: int):
#         raise HTTPException(status_code=500, detail="Cache/DB error")

#     monkeypatch.setattr(game, "get_game_from_rawg", mock_get_game_from_rawg)

#     game_id = 1
    
#     # Realizar la solicitud a la API
#     response = client.get(f"/rawg/games/{game_id}")
    
#     # Comprobaciones
#     assert response.status_code == 500
#     assert response.json() == {"detail": "Cache/DB error"}

# ----------------------------------------------------------------------
# ENDPOINTS DE users
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, user_data):
    response = await client.post("/users/", json=user_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]