import pytest


class TestClientEndpoints:
    @pytest.mark.asyncio
    async def test_create_client(self, auth_client):
        res = await auth_client.post("/api/v1/clients", json={
            "name": "Acme Corp", "company_name": "Acme Inc.", "email": "info@acme.com"
        })
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Acme Corp"
        assert data["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_list_clients(self, auth_client):
        await auth_client.post("/api/v1/clients", json={"name": "Client A"})
        await auth_client.post("/api/v1/clients", json={"name": "Client B"})
        res = await auth_client.get("/api/v1/clients")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 2

    @pytest.mark.asyncio
    async def test_get_client(self, auth_client):
        create_res = await auth_client.post("/api/v1/clients", json={"name": "Detail Client"})
        client_id = create_res.json()["id"]
        res = await auth_client.get(f"/api/v1/clients/{client_id}")
        assert res.status_code == 200
        assert res.json()["name"] == "Detail Client"

    @pytest.mark.asyncio
    async def test_update_client(self, auth_client):
        create_res = await auth_client.post("/api/v1/clients", json={"name": "Old Name"})
        client_id = create_res.json()["id"]
        res = await auth_client.patch(f"/api/v1/clients/{client_id}", json={"name": "New Name"})
        assert res.status_code == 200
        assert res.json()["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_archive_client(self, auth_client):
        create_res = await auth_client.post("/api/v1/clients", json={"name": "To Archive"})
        client_id = create_res.json()["id"]
        res = await auth_client.delete(f"/api/v1/clients/{client_id}")
        assert res.status_code == 200
        assert res.json()["status"] == "ARCHIVED"

    @pytest.mark.asyncio
    async def test_search_clients(self, auth_client):
        await auth_client.post("/api/v1/clients", json={"name": "UniqueSearchTerm"})
        res = await auth_client.get("/api/v1/clients?search=UniqueSearchTerm")
        assert res.status_code == 200
        assert res.json()["total"] >= 1

    @pytest.mark.asyncio
    async def test_client_not_found(self, auth_client):
        res = await auth_client.get("/api/v1/clients/nonexistent-id")
        assert res.status_code in [404, 400]

    @pytest.mark.asyncio
    async def test_client_data_isolation(self, client, create_test_user):
        # User 1 creates a client
        user1, token1 = await create_test_user(email="user1@test.com")
        client.headers["Authorization"] = f"Bearer {token1}"
        res = await client.post("/api/v1/clients", json={"name": "User1 Client"})
        client_id = res.json()["id"]

        # User 2 cannot see it
        user2, token2 = await create_test_user(email="user2@test.com")
        client.headers["Authorization"] = f"Bearer {token2}"
        res = await client.get(f"/api/v1/clients/{client_id}")
        assert res.status_code in [404, 400, 403]
