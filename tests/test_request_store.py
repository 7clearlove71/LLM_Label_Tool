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
