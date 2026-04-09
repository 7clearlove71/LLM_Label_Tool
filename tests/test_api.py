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

@pytest.mark.asyncio
async def test_file_read_api(sample_data_dir):
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        path = str(sample_data_dir / "sft_data" / "chat.jsonl")
        resp = await client.post("/api/file/read", json={"path": path, "offset": 0, "limit": 10})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["rows"]) == 10
        assert body["total"] == 25
        assert "schema" in body
        assert len(body["schema"]["fields"]) > 0

@pytest.mark.asyncio
async def test_file_read_all_api(sample_data_dir):
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        path = str(sample_data_dir / "instruct.json")
        resp = await client.post("/api/file/read-all", json={"path": path})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["rows"]) == 10
        assert body["total"] == 10

@pytest.mark.asyncio
async def test_file_update_api(sample_data_dir):
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        path = str(sample_data_dir / "instruct.json")
        new_data = {"instruction": "更新", "input": "x", "output": "y"}
        resp = await client.post("/api/file/update", json={
            "path": path, "row_index": 0, "data": new_data
        })
        assert resp.status_code == 200
        resp2 = await client.post("/api/file/read", json={"path": path, "offset": 0, "limit": 1})
        assert resp2.json()["rows"][0]["instruction"] == "更新"

@pytest.mark.asyncio
async def test_file_search_api(sample_data_dir):
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        path = str(sample_data_dir / "rl_data" / "preference.json")
        resp = await client.post("/api/file/search", json={
            "path": path, "keyword": "好回答5"
        })
        assert resp.status_code == 200
        assert resp.json()["count"] == 1
