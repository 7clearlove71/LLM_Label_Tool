import pytest
from httpx import AsyncClient, ASGITransport
from backend.app import create_app

@pytest.mark.asyncio
async def test_health():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
