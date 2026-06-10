import pytest
import backend.services.request_store as store_service


@pytest.mark.anyio
async def test_parse_curl_endpoint(client):
    resp = await client.post("/api/request/parse-curl", json={"text": "curl -X POST https://x.com -H 'A: 1'"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["method"] == "POST"
    assert body["url"] == "https://x.com"


@pytest.mark.anyio
async def test_parse_curl_invalid_returns_400(client):
    # 未闭合引号会让 shlex 抛 ValueError，应被路由捕获为 400 而非 500
    resp = await client.post("/api/request/parse-curl", json={"text": "curl 'unclosed"})
    assert resp.status_code == 400


@pytest.mark.anyio
async def test_to_curl_endpoint(client):
    spec = {"method": "GET", "url": "https://x.com", "headers": [{"key": "A", "value": "1", "enabled": True}]}
    resp = await client.post("/api/request/to-curl", json=spec)
    assert resp.status_code == 200
    assert "curl" in resp.json()["curl"]


@pytest.mark.anyio
async def test_requests_get_put(client, tmp_path, monkeypatch):
    monkeypatch.setattr(store_service, "REQUESTS_PATH", str(tmp_path / "requests.json"))

    empty = await client.get("/api/requests")
    assert empty.status_code == 200
    assert empty.json()["samples"] == []

    payload = {
        "samples": [{"id": "1", "name": "t", "request": {"method": "GET", "url": "http://x.com"}}],
        "draft": {"method": "POST", "url": "http://d.com"},
    }
    put = await client.put("/api/requests", json=payload)
    assert put.status_code == 200

    got = await client.get("/api/requests")
    assert got.json()["samples"][0]["name"] == "t"
    assert got.json()["draft"]["url"] == "http://d.com"
