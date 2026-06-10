import httpx
from backend.services.http_client import send_request
from backend.models import RequestSpec, KeyValueItem


def test_send_returns_status_headers_body():
    def handler(request):
        assert request.url.params.get("q") == "hi"
        return httpx.Response(200, headers={"x-test": "1", "content-type": "application/json"}, json={"ok": True})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    spec = RequestSpec(method="GET", url="http://example.com/api",
                       params=[KeyValueItem(key="q", value="hi")])
    result = send_request(spec, client=client)
    assert result.status == 200
    assert result.headers["x-test"] == "1"
    assert result.content_type.startswith("application/json")
    assert '"ok"' in result.body
    assert result.error is None
    assert result.size_bytes > 0


def test_send_disabled_param_excluded():
    seen = {}

    def handler(request):
        seen["q"] = request.url.params.get("q")
        return httpx.Response(200)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    spec = RequestSpec(url="http://x.com",
                       params=[KeyValueItem(key="q", value="hi", enabled=False)])
    send_request(spec, client=client)
    assert seen["q"] is None


def test_send_json_body_posted():
    seen = {}

    def handler(request):
        seen["content"] = request.content
        return httpx.Response(201)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    spec = RequestSpec(method="POST", url="http://x.com", body_type="json", body='{"a":1}')
    result = send_request(spec, client=client)
    assert result.status == 201
    assert seen["content"] == b'{"a":1}'


def test_send_captures_network_error():
    def handler(request):
        raise httpx.ConnectError("boom")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = send_request(RequestSpec(url="http://x.com"), client=client)
    assert result.status is None
    assert result.error


def test_send_invalid_url_captured():
    """httpx.InvalidURL（不继承自 HTTPError）也应被捕获为 error，而非冒泡成 500。"""

    class _InvalidURLTransport(httpx.BaseTransport):
        def handle_request(self, request):
            raise httpx.InvalidURL("bad url")

    client = httpx.Client(transport=_InvalidURLTransport())
    result = send_request(RequestSpec(url="http://bad-url-placeholder"), client=client)
    assert result.status is None
    assert result.error


def test_send_client_construction_error_captured(monkeypatch):
    # 模拟构造 httpx.Client 时抛异常（如环境代理缺包），应被捕获为 error 而非抛出
    import backend.services.http_client as mod

    def boom(*args, **kwargs):
        raise ImportError("Using SOCKS proxy, but the 'socksio' package is not installed.")

    monkeypatch.setattr(mod.httpx, "Client", boom)
    result = mod.send_request(RequestSpec(url="http://example.com"))
    assert result.status is None
    assert result.error
