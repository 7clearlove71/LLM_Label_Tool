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

@pytest.mark.asyncio
async def test_scan_api(sample_data_dir):
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/scan", json={"path": str(sample_data_dir)})
        assert resp.status_code == 200
        tree = resp.json()
        assert tree["type"] == "directory"
        names = {c["name"] for c in tree["children"]}
        assert "sft_data" in names

@pytest.mark.asyncio
async def test_scan_api_bad_path():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/scan", json={"path": "/nonexistent/12345"})
        assert resp.status_code == 400
