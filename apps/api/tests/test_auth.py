import pytest


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_register(self, client):
        res = await client.post(
            "/api/v1/auth/register", json={"name": "Test User", "email": "test@test.com", "password": "testpass123"}
        )
        assert res.status_code == 201
        data = res.json()
        assert data["email"] == "test@test.com"
        assert data["name"] == "Test User"
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate(self, client, create_test_user):
        await create_test_user(email="dup@test.com")
        res = await client.post(
            "/api/v1/auth/register", json={"name": "Test", "email": "dup@test.com", "password": "testpass123"}
        )
        assert res.status_code in [400, 409, 422]

    @pytest.mark.asyncio
    async def test_login(self, client, create_test_user):
        await create_test_user(email="login@test.com", password="secret123")
        res = await client.post("/api/v1/auth/login", json={"email": "login@test.com", "password": "secret123"})
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, create_test_user):
        await create_test_user(email="wrong@test.com", password="correct")
        res = await client.post("/api/v1/auth/login", json={"email": "wrong@test.com", "password": "incorrect"})
        assert res.status_code in [401, 400]

    @pytest.mark.asyncio
    async def test_get_me(self, auth_client):
        res = await auth_client.get("/api/v1/auth/me")
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == "test@test.com"

    @pytest.mark.asyncio
    async def test_update_me(self, auth_client):
        res = await auth_client.patch("/api/v1/auth/me", json={"name": "Updated"})
        assert res.status_code == 200
        assert res.json()["name"] == "Updated"

    @pytest.mark.asyncio
    async def test_get_me_unauthenticated(self, client):
        res = await client.get("/api/v1/auth/me")
        assert res.status_code == 401
