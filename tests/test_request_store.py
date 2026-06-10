import backend.services.request_store as store_service
from backend.models import RequestStore, RequestSample, RequestSpec


def test_load_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(store_service, "REQUESTS_PATH", str(tmp_path / "requests.json"))
    data = store_service.load_store()
    assert data.samples == []
    assert data.draft is None


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    path = str(tmp_path / "requests.json")
    monkeypatch.setattr(store_service, "REQUESTS_PATH", path)

    original = RequestStore(
        samples=[RequestSample(id="1", name="登录", request=RequestSpec(method="POST", url="http://x.com"))],
        draft=RequestSpec(method="GET", url="http://draft.com"),
    )
    store_service.save_store(original)

    loaded = store_service.load_store()
    assert len(loaded.samples) == 1
    assert loaded.samples[0].name == "登录"
    assert loaded.samples[0].request.method == "POST"
    assert loaded.draft.url == "http://draft.com"


import json as _json


def test_load_corrupted_file_returns_empty_and_backs_up(tmp_path, monkeypatch):
    path = tmp_path / "requests.json"
    path.write_text("{ this is not valid json", encoding="utf-8")
    monkeypatch.setattr(store_service, "REQUESTS_PATH", str(path))

    data = store_service.load_store()
    assert data.samples == []
    assert data.draft is None
    # 损坏文件应被备份，原路径不再是损坏内容
    assert (tmp_path / "requests.json.corrupt").exists()


def test_save_is_atomic_no_partial_temp_left(tmp_path, monkeypatch):
    path = tmp_path / "requests.json"
    monkeypatch.setattr(store_service, "REQUESTS_PATH", str(path))

    store_service.save_store(RequestStore(
        samples=[RequestSample(id="1", name="t", request=RequestSpec(url="http://x.com"))],
        draft=None,
    ))
    # 写完后目录里不应残留临时文件，只有目标文件
    leftovers = [p.name for p in tmp_path.iterdir() if p.name != "requests.json"]
    assert leftovers == []
    # 内容可正常读回
    loaded = store_service.load_store()
    assert loaded.samples[0].name == "t"


def test_save_and_load_preserves_active_id(tmp_path, monkeypatch):
    path = str(tmp_path / "requests.json")
    monkeypatch.setattr(store_service, "REQUESTS_PATH", path)

    store_service.save_store(RequestStore(
        samples=[RequestSample(id="abc", name="t", request=RequestSpec(url="http://x.com"))],
        active_id="abc",
    ))
    loaded = store_service.load_store()
    assert loaded.active_id == "abc"


def test_load_legacy_file_without_active_id(tmp_path, monkeypatch):
    path = tmp_path / "requests.json"
    path.write_text(
        '{"samples": [], "draft": {"method": "GET", "url": "http://old.com"}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(store_service, "REQUESTS_PATH", str(path))

    loaded = store_service.load_store()
    assert loaded.active_id is None
    assert loaded.draft.url == "http://old.com"
