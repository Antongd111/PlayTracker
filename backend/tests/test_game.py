# import pytest
# import httpx
# from fastapi import HTTPException
# from app.services import game

# # ----------------------------------------------------------------------
# # Formateo de juegos
# # ----------------------------------------------------------------------
# @pytest.mark.asyncio
# async def test_format_game_maps_fields_correctly():
#     raw = {
#         "id": 123,
#         "name": "The Witcher 3",
#         "released": "2015-05-19",
#         "background_image": "img.jpg",
#         "rating": 4.8,
#     }
#     result = game.format_game(raw)

#     assert result == {
#         "id": 123,
#         "title": "The Witcher 3",
#         "year": 2015,
#         "imageUrl": "img.jpg",
#         "rating": 4.8,
#     }


# # ----------------------------------------------------------------------
# # Formateo de juegos (faltan campos)
# # ----------------------------------------------------------------------
# @pytest.mark.asyncio
# async def test_format_game_handles_missing_fields():
#     raw = {"id": 1, "name": "Untitled", "rating": None}
#     result = game.format_game(raw)
#     assert result["year"] == 0
#     assert result["imageUrl"] == ""
#     assert result["rating"] == None


# # ----------------------------------------------------------------------
# # Formateo de juegos (todos los campos)
# # ----------------------------------------------------------------------
# @pytest.mark.asyncio
# async def test_format_game_detail_maps_complex_fields():
#     g = {
#         "id": 10,
#         "name": "Zelda",
#         "description_raw": "Epic adventure",
#         "released": "2023-03-01",
#         "background_image": "zelda.jpg",
#         "rating": 4.9,
#         "platforms": [{"platform": {"name": "Switch"}}],
#         "genres": [{"name": "Action"}],
#         "developers": [{"name": "Nintendo"}],
#         "publishers": [{"name": "Nintendo"}],
#         "tags": [{"name": "Fantasy"}],
#         "esrb_rating": {"name": "Teen"},
#         "metacritic": 96,
#         "metacritic_url": "https://meta",
#         "website": "https://zelda.com",
#     }
#     screenshots = {"results": [{"image": "s1.png"}, {"image": "s2.png"}]}
#     trailers = {"results": [{"data": {"480": "t1.mp4"}}]}
#     similar = {"results": [{"id": 11, "name": "Zelda 2", "background_image": "z2.png"}]}

#     out = game.format_game_detail(g, screenshots, trailers, similar)
#     assert out["id"] == 10
#     assert "Zelda" in out["title"]
#     assert "Switch" in out["platforms"]
#     assert out["screenshots"] == ["s1.png", "s2.png"]
#     assert out["videos"] == ["t1.mp4"]
#     assert out["similarGames"][0]["id"] == 11


# # ----------------------------------------------------------------------
# # Búsqueda de juegos
# # ----------------------------------------------------------------------
# @pytest.mark.asyncio
# async def test_search_games_returns_formatted_results(monkeypatch):
#     mock_json = {"results": [{"id": 1, "name": "Halo", "released": "2001-11-15"}]}

#     class MockResponse:
#         status_code = 200
#         def json(self): return mock_json

#     async def mock_get(path, params=None):
#         return MockResponse()

#     monkeypatch.setattr(game, "_rawg_get", mock_get)

#     results = await game.search_games("Halo")
#     assert len(results) == 1
#     assert results[0]["title"] == "Halo"


# # ----------------------------------------------------------------------
# # Búsqueda de juegos (error)
# # ----------------------------------------------------------------------
# @pytest.mark.asyncio
# async def test_search_games_raises_on_error(monkeypatch):
#     class MockResponse:
#         status_code = 500
#         def json(self): return {}

#     async def mock_get(path, params=None):
#         return MockResponse()

#     monkeypatch.setattr(game, "_rawg_get", mock_get)

#     with pytest.raises(HTTPException):
#         await game.search_games("Halo")


# # ----------------------------------------------------------------------
# # Obtener juego de rawg
# # ----------------------------------------------------------------------
# @pytest.mark.asyncio
# async def test_get_game_from_rawg(monkeypatch):
#     class MockResponse:
#         def __init__(self, json_data, status_code=200):
#             self._json = json_data
#             self.status_code = status_code
#         def json(self): return self._json

#     async def mock_get(path, params=None):
#         if path.endswith("/screenshots"):
#             return MockResponse({"results": [{"image": "s1.png"}]})
#         elif path.endswith("/movies"):
#             return MockResponse({"results": [{"data": {"480": "v1.mp4"}}]})
#         elif path.endswith("/suggested"):
#             return MockResponse({"results": [{"id": 2, "name": "Halo 2"}]})
#         else:
#             return MockResponse({
#                 "id": 1, "name": "Halo", "released": "2001-11-15",
#                 "description_raw": "FPS", "platforms": [], "genres": []
#             })

#     monkeypatch.setattr(game, "_rawg_get", mock_get)

#     result = await game.get_game_from_rawg(1)
#     assert result["id"] == 1
#     assert "Halo" in result["title"]
#     assert result["screenshots"] == ["s1.png"]
#     assert result["videos"] == ["v1.mp4"]
#     assert result["similarGames"][0]["id"] == 2


# # ----------------------------------------------------------------------
# # Obtener juego de rawg (error)
# # ----------------------------------------------------------------------
# @pytest.mark.asyncio
# async def test_get_game_from_rawg_raises_on_error(monkeypatch):
#     class MockResponse:
#         status_code = 404
#         def json(self): return {}

#     async def mock_get(path, params=None): return MockResponse()

#     monkeypatch.setattr(game, "_rawg_get", mock_get)

#     with pytest.raises(HTTPException):
#         await game.get_game_from_rawg(999)


# # ----------------------------------------------------------------------
# # Obtener juegos populares de rawg
# # ----------------------------------------------------------------------
# @pytest.mark.asyncio
# async def test_get_popular_games_returns_list(monkeypatch):
#     mock_json = {"results": [{"id": 5, "name": "GTA V", "released": "2013-09-17"}]}

#     class MockResponse:
#         status_code = 200
#         def json(self): return mock_json

#     async def mock_get(path, params=None):
#         assert path == "/games"
#         return MockResponse()

#     monkeypatch.setattr(game, "_rawg_get", mock_get)

#     result = await game.get_popular_games()
#     assert isinstance(result, list)
#     assert result[0]["title"] == "GTA V"


# # ----------------------------------------------------------------------
# # Obtener géneros
# # ----------------------------------------------------------------------
# @pytest.mark.asyncio
# async def test_get_genres(monkeypatch):
#     mock_json = {"results": [{"name": "Action"}]}

#     class MockResponse:
#         status_code = 200
#         def json(self): return mock_json

#     async def mock_get(path, params=None):
#         assert path == "/genres"
#         return MockResponse()

#     monkeypatch.setattr(game, "_rawg_get", mock_get)

#     res = await game.get_genres()
#     assert "results" in res
#     assert res["results"][0]["name"] == "Action"


# # ----------------------------------------------------------------------
# # Obtener géneros (error)
# # ----------------------------------------------------------------------
# @pytest.mark.asyncio
# async def test_get_genres_raises_on_error(monkeypatch):
#     class MockResponse:
#         status_code = 500
#         def json(self): return {}

#     async def mock_get(path, params=None): return MockResponse()

#     monkeypatch.setattr(game, "_rawg_get", mock_get)
#     with pytest.raises(HTTPException):
#         await game.get_genres()


# # ----------------------------------------------------------------------
# # Obtener lista de juegos por géneros
# # ----------------------------------------------------------------------
# @pytest.mark.asyncio
# async def test_list_games_by_genres(monkeypatch):
#     mock_json = {"results": [{"id": 1, "name": "DOOM"}]}

#     class MockResponse:
#         status_code = 200
#         def json(self): return mock_json

#     async def mock_get(path, params=None):
#         assert "genres" in params
#         return MockResponse()

#     monkeypatch.setattr(game, "_rawg_get", mock_get)
#     res = await game.list_games_by_genres(["Action", "Shooter"])
#     assert res[0]["name"] == "DOOM"


# # ----------------------------------------------------------------------
# # Obtener lista de juegos por géneros (error)
# # ----------------------------------------------------------------------
# @pytest.mark.asyncio
# async def test_list_games_by_genres_returns(monkeypatch):
#     class MockResponse:
#         status_code = 500
#         def json(self): return {}

#     async def mock_get(path, params=None): return MockResponse()

#     monkeypatch.setattr(game, "_rawg_get", mock_get)
#     res = await game.list_games_by_genres(["Action"])
#     assert res == []
