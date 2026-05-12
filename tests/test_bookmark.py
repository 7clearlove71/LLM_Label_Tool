import json
import pytest
import backend.services.bookmark as bookmark_service
from backend.models import BookmarksData


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------

def test_load_bookmarks_file_not_exist(tmp_path, monkeypatch):
    """当 bookmarks.json 不存在时，返回空 BookmarksData。"""
    monkeypatch.setattr(bookmark_service, "BOOKMARKS_PATH", str(tmp_path / "bookmarks.json"))
    data = bookmark_service.load_bookmarks()
    assert data.default is None
    assert data.bookmarks == []


def test_save_and_load_bookmarks(tmp_path, monkeypatch):
    """保存后再加载，数据一致（round-trip）。"""
    path = str(tmp_path / "bookmarks.json")
    monkeypatch.setattr(bookmark_service, "BOOKMARKS_PATH", path)

    original = BookmarksData(default="/data/default", bookmarks=["/data/a", "/data/b"])
    bookmark_service.save_bookmarks(original)

    loaded = bookmark_service.load_bookmarks()
    assert loaded.default == "/data/default"
    assert loaded.bookmarks == ["/data/a", "/data/b"]


def test_save_bookmarks_limit(tmp_path, monkeypatch):
    """超过 10 条书签时，只保留前 10 条。"""
    path = str(tmp_path / "bookmarks.json")
    monkeypatch.setattr(bookmark_service, "BOOKMARKS_PATH", path)

    many = BookmarksData(bookmarks=[f"/data/{i}" for i in range(15)])
    result = bookmark_service.save_bookmarks(many)
    assert len(result.bookmarks) == 10
    assert result.bookmarks == [f"/data/{i}" for i in range(10)]

    loaded = bookmark_service.load_bookmarks()
    assert len(loaded.bookmarks) == 10


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_bookmarks_empty(client, tmp_path, monkeypatch):
    """GET /api/bookmarks 在没有文件时返回空数据。"""
    monkeypatch.setattr(bookmark_service, "BOOKMARKS_PATH", str(tmp_path / "bookmarks.json"))
    resp = await client.get("/api/bookmarks")
    assert resp.status_code == 200
    body = resp.json()
    assert body["default"] is None
    assert body["bookmarks"] == []


@pytest.mark.anyio
async def test_put_bookmarks(client, tmp_path, monkeypatch):
    """PUT /api/bookmarks 保存数据，GET 能取回相同数据。"""
    monkeypatch.setattr(bookmark_service, "BOOKMARKS_PATH", str(tmp_path / "bookmarks.json"))

    payload = {"default": "/data/default", "bookmarks": ["/data/a", "/data/b"]}
    put_resp = await client.put("/api/bookmarks", json=payload)
    assert put_resp.status_code == 200
    assert put_resp.json()["default"] == "/data/default"
    assert put_resp.json()["bookmarks"] == ["/data/a", "/data/b"]

    get_resp = await client.get("/api/bookmarks")
    assert get_resp.status_code == 200
    assert get_resp.json()["default"] == "/data/default"
    assert get_resp.json()["bookmarks"] == ["/data/a", "/data/b"]
