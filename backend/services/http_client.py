import time
import httpx
from typing import Optional
from backend.models import RequestSpec, ResponseResult

DEFAULT_TIMEOUT = 30.0
MAX_BODY_BYTES = 2 * 1024 * 1024


def send_request(spec: RequestSpec, client: Optional[httpx.Client] = None) -> ResponseResult:
    headers = {h.key: h.value for h in spec.headers if h.enabled and h.key}
    params = {p.key: p.value for p in spec.params if p.enabled and p.key}

    content = None
    data = None
    if spec.body_type in ("json", "raw") and spec.body:
        content = spec.body.encode("utf-8")
    elif spec.body_type == "form":
        data = {f.key: f.value for f in spec.form_body if f.enabled and f.key}

    owns_client = client is None
    if owns_client:
        client = httpx.Client(timeout=DEFAULT_TIMEOUT, follow_redirects=True)

    try:
        start = time.perf_counter()
        resp = client.request(
            spec.method.upper() or "GET",
            spec.url,
            params=params or None,
            headers=headers or None,
            content=content,
            data=data,
        )
        elapsed = (time.perf_counter() - start) * 1000
        raw = resp.content
        size = len(raw)
        text = resp.text
        truncated = False
        if len(text) > MAX_BODY_BYTES:
            text = text[:MAX_BODY_BYTES]
            truncated = True
        return ResponseResult(
            status=resp.status_code,
            status_text=resp.reason_phrase,
            elapsed_ms=round(elapsed, 1),
            size_bytes=size,
            headers=dict(resp.headers),
            content_type=resp.headers.get("content-type", ""),
            body=text,
            truncated=truncated,
        )
    except (httpx.HTTPError, httpx.InvalidURL) as e:
        return ResponseResult(error=str(e) or e.__class__.__name__)
    finally:
        if owns_client:
            client.close()
