# import pytest

# @pytest.mark.anyio
# async def test_register_and_login_flow(client):
#     # Registro
#     res = await client.post("/auth/register", json={
#         "email": "alice@example.com",
#         "password": "secret123",
#         "username": "alice"
#     })
#     assert res.status_code == 201
#     data = res.json()
#     assert "id" in data and data["email"] == "alice@example.com"

#     # Login
#     res = await client.post("/auth/login", data={
#         "username": "alice@example.com",
#         "password": "secret123"
#     })
#     assert res.status_code == 200
#     token = res.json()["access_token"]
#     assert token
