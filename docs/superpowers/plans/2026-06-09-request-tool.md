# 请求工具（功能二）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为个人工作空间站新增一个类似 Postman 的本地 HTTP 请求调试工具，支持构建/发送请求、查看响应、保存样例、curl 导入导出。

**Architecture:** 后端 FastAPI 用 httpx 代理发出请求（规避 CORS），curl 解析/生成与样例持久化均在后端；前端 Vue 3 顶部 Tab 在「数据查看器 / 请求工具」两个模块间切换，请求工具左侧样例列表 + 右侧请求构建/响应面板，面板编辑防抖自动保存草稿。

**Tech Stack:** Python FastAPI + httpx + pydantic + pytest；Vue 3 + Vite + Element Plus。

---

## 文件结构

**后端（新增/修改）**
- Modify `backend/models.py` — 新增 `KeyValueItem` / `RequestSpec` / `ResponseResult` / `RequestSample` / `RequestStore` / `CurlText` / `CurlResult`
- Create `backend/services/curl_parser.py` — `parse_curl` / `to_curl`
- Create `backend/services/http_client.py` — `send_request`
- Create `backend/services/request_store.py` — `load_store` / `save_store`
- Create `backend/routers/request.py` — 5 个接口
- Modify `backend/app.py` — `include_router(request.router)`
- Create `tests/test_curl_parser.py` / `tests/test_http_client.py` / `tests/test_request_store.py` / `tests/test_request_api.py`

**前端（新增/修改）**
- Modify `frontend/src/api/index.js` — 5 个 api 函数
- Modify `frontend/src/App.vue` — 顶部 Tab + 模块切换
- Create `frontend/src/modules/ViewerModule.vue` — 现有查看器抽取
- Create `frontend/src/modules/RequestModule.vue` — 请求工具左右布局 + 草稿自动保存
- Create `frontend/src/components/request/KeyValueEditor.vue`
- Create `frontend/src/components/request/BodyEditor.vue`
- Create `frontend/src/components/request/RequestBuilder.vue`
- Create `frontend/src/components/request/ResponseView.vue`
- Create `frontend/src/components/request/CurlImportDialog.vue`
- Create `frontend/src/components/request/SampleList.vue`

---

## Task 1: 数据模型

**Files:**
- Modify: `backend/models.py`
- Test: `tests/test_request_models.py`

- [ ] **Step 1: 写失败测试**

`tests/test_request_models.py`：
```python
from backend.models import RequestSpec, ResponseResult, RequestStore, KeyValueItem


def test_request_spec_defaults():
    spec = RequestSpec()
    assert spec.method == "GET"
    assert spec.url == ""
    assert spec.params == []
    assert spec.headers == []
    assert spec.body_type == "none"
    assert spec.body == ""
    assert spec.form_body == []


def test_request_store_defaults():
    store = RequestStore()
    assert store.samples == []
    assert store.draft is None


def test_key_value_item_default_enabled():
    item = KeyValueItem(key="k", value="v")
    assert item.enabled is True


def test_response_result_error_shape():
    r = ResponseResult(error="boom")
    assert r.status is None
    assert r.error == "boom"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_request_models.py -v`
Expected: FAIL（`ImportError: cannot import name 'RequestSpec'`）

- [ ] **Step 3: 实现模型**

在 `backend/models.py` 末尾追加：
```python
class KeyValueItem(BaseModel):
    key: str = ""
    value: str = ""
    enabled: bool = True


class RequestSpec(BaseModel):
    method: str = "GET"
    url: str = ""
    params: list[KeyValueItem] = []
    headers: list[KeyValueItem] = []
    body_type: str = "none"        # none | json | raw | form
    body: str = ""                 # json/raw 文本内容
    form_body: list[KeyValueItem] = []


class ResponseResult(BaseModel):
    status: Optional[int] = None
    status_text: str = ""
    elapsed_ms: float = 0
    size_bytes: int = 0
    headers: dict[str, str] = {}
    content_type: str = ""
    body: str = ""
    truncated: bool = False
    error: Optional[str] = None


class RequestSample(BaseModel):
    id: str
    name: str
    request: RequestSpec


class RequestStore(BaseModel):
    samples: list[RequestSample] = []
    draft: Optional[RequestSpec] = None


class CurlText(BaseModel):
    text: str


class CurlResult(BaseModel):
    curl: str
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_request_models.py -v`
Expected: PASS（4 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/models.py tests/test_request_models.py
git commit -m "feat: 请求工具数据模型"
```

---

## Task 2: curl 解析（parse_curl）

**Files:**
- Create: `backend/services/curl_parser.py`
- Test: `tests/test_curl_parser.py`

- [ ] **Step 1: 写失败测试**

`tests/test_curl_parser.py`：
```python
from backend.services.curl_parser import parse_curl


def test_parse_simple_get():
    spec = parse_curl("curl https://api.example.com/users")
    assert spec.method == "GET"
    assert spec.url == "https://api.example.com/users"


def test_parse_without_curl_prefix():
    spec = parse_curl("https://api.example.com/users")
    assert spec.url == "https://api.example.com/users"


def test_parse_method_and_headers():
    spec = parse_curl('curl -X POST https://api.example.com/login -H "Content-Type: application/json" -H "Authorization: Bearer abc"')
    assert spec.method == "POST"
    headers = {h.key: h.value for h in spec.headers}
    assert headers["Content-Type"] == "application/json"
    assert headers["Authorization"] == "Bearer abc"


def test_parse_data_implies_post_and_json():
    spec = parse_curl('curl https://x.com -H "content-type: application/json" --data-raw \'{"a":1}\'')
    assert spec.method == "POST"
    assert spec.body == '{"a":1}'
    assert spec.body_type == "json"


def test_parse_data_non_json_is_raw():
    spec = parse_curl("curl https://x.com -d hello")
    assert spec.method == "POST"
    assert spec.body == "hello"
    assert spec.body_type == "raw"


def test_parse_multiline_continuation():
    text = "curl https://x.com \\\n  -X PUT \\\n  -H 'A: 1'"
    spec = parse_curl(text)
    assert spec.method == "PUT"
    assert spec.url == "https://x.com"
    assert spec.headers[0].key == "A"


def test_parse_url_flag():
    spec = parse_curl("curl --url https://x.com/a")
    assert spec.url == "https://x.com/a"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_curl_parser.py -v`
Expected: FAIL（`ModuleNotFoundError: backend.services.curl_parser`）

- [ ] **Step 3: 实现 parse_curl**

`backend/services/curl_parser.py`：
```python
import shlex
from backend.models import RequestSpec, KeyValueItem

_DATA_FLAGS = ("-d", "--data", "--data-raw", "--data-binary", "--data-ascii")


def parse_curl(text: str) -> RequestSpec:
    # 去掉行末续行符
    text = text.replace("\\\r\n", " ").replace("\\\n", " ")
    tokens = shlex.split(text)
    if tokens and tokens[0] == "curl":
        tokens = tokens[1:]

    method = None
    url = None
    body = None
    headers: list[KeyValueItem] = []

    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in ("-X", "--request") and i + 1 < len(tokens):
            method = tokens[i + 1]
            i += 2
            continue
        if t in ("-H", "--header") and i + 1 < len(tokens):
            raw = tokens[i + 1]
            i += 2
            if ":" in raw:
                k, v = raw.split(":", 1)
                headers.append(KeyValueItem(key=k.strip(), value=v.strip()))
            continue
        if t in _DATA_FLAGS and i + 1 < len(tokens):
            body = tokens[i + 1]
            i += 2
            continue
        if t == "--url" and i + 1 < len(tokens):
            url = tokens[i + 1]
            i += 2
            continue
        if t.startswith("-"):
            # 未知 flag，跳过（MVP 不处理其携带的值）
            i += 1
            continue
        if url is None:
            url = t
        i += 1

    spec = RequestSpec(url=url or "", headers=headers)
    if method:
        spec.method = method.upper()
    elif body is not None:
        spec.method = "POST"

    if body is not None:
        spec.body = body
        content_type = next((h.value for h in headers if h.key.lower() == "content-type"), "")
        spec.body_type = "json" if "json" in content_type.lower() else "raw"

    return spec
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_curl_parser.py -v`
Expected: PASS（7 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/services/curl_parser.py tests/test_curl_parser.py
git commit -m "feat: curl 解析器 parse_curl"
```

---

## Task 3: curl 生成（to_curl）+ 往返一致性

**Files:**
- Modify: `backend/services/curl_parser.py`
- Test: `tests/test_curl_parser.py`

- [ ] **Step 1: 追加失败测试**

在 `tests/test_curl_parser.py` 末尾追加：
```python
from backend.services.curl_parser import to_curl
from backend.models import RequestSpec, KeyValueItem


def test_to_curl_get_with_header():
    spec = RequestSpec(method="GET", url="https://x.com/a",
                       headers=[KeyValueItem(key="Accept", value="application/json")])
    out = to_curl(spec)
    assert out.startswith("curl ")
    assert "'https://x.com/a'" in out
    assert "-H 'Accept: application/json'" in out
    assert "-X" not in out  # GET 不显式写 -X


def test_to_curl_post_json_body():
    spec = RequestSpec(method="POST", url="https://x.com",
                       body_type="json", body='{"a":1}')
    out = to_curl(spec)
    assert "-X POST" in out
    assert "--data-raw '{\"a\":1}'" in out


def test_to_curl_appends_params():
    spec = RequestSpec(method="GET", url="https://x.com/a",
                       params=[KeyValueItem(key="q", value="hi")])
    out = to_curl(spec)
    assert "q=hi" in out


def test_roundtrip_post_json():
    spec = RequestSpec(method="POST", url="https://x.com/login",
                       headers=[KeyValueItem(key="Content-Type", value="application/json")],
                       body_type="json", body='{"u":"a"}')
    again = parse_curl(to_curl(spec))
    assert again.method == "POST"
    assert again.url == "https://x.com/login"
    assert again.body == '{"u":"a"}'
    assert {h.key: h.value for h in again.headers}["Content-Type"] == "application/json"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_curl_parser.py -k "to_curl or roundtrip" -v`
Expected: FAIL（`ImportError: cannot import name 'to_curl'`）

- [ ] **Step 3: 实现 to_curl**

在 `backend/services/curl_parser.py` 顶部 import 处增加：
```python
from urllib.parse import urlencode
```
文件末尾追加：
```python
def _quote(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"


def to_curl(spec: RequestSpec) -> str:
    parts = ["curl"]
    if spec.method and spec.method.upper() != "GET":
        parts += ["-X", spec.method.upper()]

    url = spec.url
    enabled_params = [(p.key, p.value) for p in spec.params if p.enabled and p.key]
    if enabled_params:
        sep = "&" if "?" in url else "?"
        url = url + sep + urlencode(enabled_params)
    parts.append(_quote(url))

    for h in spec.headers:
        if h.enabled and h.key:
            parts += ["-H", _quote(f"{h.key}: {h.value}")]

    if spec.body_type in ("json", "raw") and spec.body:
        parts += ["--data-raw", _quote(spec.body)]
    elif spec.body_type == "form":
        data = urlencode([(f.key, f.value) for f in spec.form_body if f.enabled and f.key])
        if data:
            parts += ["--data", _quote(data)]

    return " ".join(parts)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_curl_parser.py -v`
Expected: PASS（11 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/services/curl_parser.py tests/test_curl_parser.py
git commit -m "feat: curl 生成 to_curl 与往返一致性"
```

---

## Task 4: HTTP 发送（send_request）

**Files:**
- Create: `backend/services/http_client.py`
- Test: `tests/test_http_client.py`

- [ ] **Step 1: 写失败测试**

`tests/test_http_client.py`：
```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_http_client.py -v`
Expected: FAIL（`ModuleNotFoundError: backend.services.http_client`）

- [ ] **Step 3: 实现 send_request**

`backend/services/http_client.py`：
```python
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
    except httpx.HTTPError as e:
        return ResponseResult(error=str(e) or e.__class__.__name__)
    finally:
        if owns_client:
            client.close()
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_http_client.py -v`
Expected: PASS（4 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/services/http_client.py tests/test_http_client.py
git commit -m "feat: httpx 代理发送 send_request"
```

---

## Task 5: 样例与草稿持久化（request_store）

**Files:**
- Create: `backend/services/request_store.py`
- Test: `tests/test_request_store.py`

- [ ] **Step 1: 写失败测试**

`tests/test_request_store.py`：
```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_request_store.py -v`
Expected: FAIL（`ModuleNotFoundError: backend.services.request_store`）

- [ ] **Step 3: 实现 request_store**

`backend/services/request_store.py`：
```python
import json
import os
from backend.models import RequestStore

REQUESTS_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "requests.json")
)


def load_store() -> RequestStore:
    if not os.path.isfile(REQUESTS_PATH):
        return RequestStore()
    with open(REQUESTS_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return RequestStore(**raw)


def save_store(data: RequestStore) -> RequestStore:
    with open(REQUESTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data.model_dump(), f, ensure_ascii=False, indent=2)
    return data
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_request_store.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/services/request_store.py tests/test_request_store.py
git commit -m "feat: 请求样例与草稿持久化 request_store"
```

---

## Task 6: 路由装配 + API 测试

**Files:**
- Create: `backend/routers/request.py`
- Modify: `backend/app.py`
- Test: `tests/test_request_api.py`

- [ ] **Step 1: 写失败测试**

`tests/test_request_api.py`：
```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_request_api.py -v`
Expected: FAIL（404，路由未注册）

- [ ] **Step 3: 实现路由并装配**

`backend/routers/request.py`：
```python
from fastapi import APIRouter
from backend.models import RequestSpec, ResponseResult, RequestStore, CurlText, CurlResult
from backend.services.http_client import send_request
from backend.services.curl_parser import parse_curl, to_curl
from backend.services.request_store import load_store, save_store

router = APIRouter()


@router.post("/api/request/send")
def send(spec: RequestSpec) -> ResponseResult:
    return send_request(spec)


@router.post("/api/request/parse-curl")
def parse(payload: CurlText) -> RequestSpec:
    return parse_curl(payload.text)


@router.post("/api/request/to-curl")
def export(spec: RequestSpec) -> CurlResult:
    return CurlResult(curl=to_curl(spec))


@router.get("/api/requests")
def get_requests() -> RequestStore:
    return load_store()


@router.put("/api/requests")
def put_requests(data: RequestStore) -> RequestStore:
    return save_store(data)
```

`backend/app.py` 修改 import 行与注册行：
```python
from backend.routers import scan, file, bookmark, request
```
```python
    app.include_router(bookmark.router)
    app.include_router(request.router)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_request_api.py -v`
Expected: PASS（3 passed）

- [ ] **Step 5: 全量后端回归**

Run: `python -m pytest tests/ -v`
Expected: 全部 PASS（含原有测试）

- [ ] **Step 6: 提交**

```bash
git add backend/routers/request.py backend/app.py tests/test_request_api.py
git commit -m "feat: 请求工具后端路由装配"
```

---

## Task 7: 前端 API 封装

**Files:**
- Modify: `frontend/src/api/index.js`

- [ ] **Step 1: 追加 api 函数**

在 `frontend/src/api/index.js` 末尾追加：
```javascript
export function sendRequest(spec) {
  return api.post('/api/request/send', spec)
}

export function parseCurl(text) {
  return api.post('/api/request/parse-curl', { text })
}

export function toCurl(spec) {
  return api.post('/api/request/to-curl', spec)
}

export function getRequestSamples() {
  return api.get('/api/requests')
}

export function saveRequestSamples(data) {
  return api.put('/api/requests', data)
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/api/index.js
git commit -m "feat: 前端请求工具 api 封装"
```

---

## Task 8: 模块导航（顶部 Tab + ViewerModule 抽取）

**Files:**
- Create: `frontend/src/modules/ViewerModule.vue`
- Modify: `frontend/src/App.vue`
- Create: `frontend/src/modules/RequestModule.vue`（占位，Task 14 完善）

- [ ] **Step 1: 创建 ViewerModule.vue（迁移现有查看器逻辑）**

`frontend/src/modules/ViewerModule.vue`（把当前 `App.vue` 的查看器部分整体搬入）：
```vue
<template>
  <div class="viewer-module">
    <aside class="sidebar" :style="{ width: sidebarWidth + 'px' }">
      <PathInput @scan="onScan" />
      <FileTree :tree="fileTree" @select="onFileSelect" />
    </aside>
    <div class="resize-handle" @mousedown="startResize"></div>
    <main class="main-content">
      <div class="viewer-toolbar" v-if="selectedFile">
        <button class="nav-link-btn" @click="showSaveAsDialog = true">另存为</button>
      </div>
      <DataView :file-path="selectedFile" :key="selectedFile" />
    </main>

    <el-dialog v-model="showSaveAsDialog" title="另存为" width="500px">
      <el-input v-model="saveAsPath" placeholder="输入目标文件路径" />
      <template #footer>
        <el-button @click="showSaveAsDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveAs">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import PathInput from '../components/PathInput.vue'
import FileTree from '../components/FileTree.vue'
import DataView from '../components/DataView.vue'
import { scanDirectory, saveAs } from '../api'

const fileTree = ref(null)
const selectedFile = ref('')
const sidebarWidth = ref(260)
const showSaveAsDialog = ref(false)
const saveAsPath = ref('')

async function onScan(path) {
  const { data } = await scanDirectory(path)
  fileTree.value = data
}

function onFileSelect(filePath) {
  selectedFile.value = filePath
}

async function handleSaveAs() {
  try {
    await saveAs(selectedFile.value, saveAsPath.value)
    ElMessage.success('已另存为 ' + saveAsPath.value)
    showSaveAsDialog.value = false
  } catch (e) {
    ElMessage.error('另存为失败：' + (e.response?.data?.detail || e.message))
  }
}

function startResize(e) {
  e.preventDefault()
  const startX = e.clientX
  const startWidth = sidebarWidth.value
  function onMouseMove(ev) {
    const delta = ev.clientX - startX
    sidebarWidth.value = Math.min(480, Math.max(180, startWidth + delta))
  }
  function onMouseUp() {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}
</script>

<style scoped>
.viewer-module { display: flex; flex: 1; min-height: 0; }
.sidebar { flex-shrink: 0; overflow: auto; border-right: 1px solid rgba(0,0,0,0.08); }
.resize-handle { width: 5px; cursor: col-resize; background: transparent; }
.resize-handle:hover { background: rgba(0,122,255,0.2); }
.main-content { flex: 1; min-width: 0; overflow: auto; display: flex; flex-direction: column; }
.viewer-toolbar { padding: 8px 16px; text-align: right; }
.nav-link-btn { background: none; border: none; color: #007aff; cursor: pointer; font-size: 14px; }
</style>
```
> 注：上面的 `<style>` 是从原 `App.vue` 的对应规则迁移而来。实现时请对照原 `App.vue` 的 `<style>`，把 `.sidebar` / `.resize-handle` / `.main-content` / `.nav-link-btn` 等查看器相关样式原样搬入本组件，保持视觉不变。

- [ ] **Step 2: 创建 RequestModule 占位**

`frontend/src/modules/RequestModule.vue`：
```vue
<template>
  <div class="request-module">请求工具（建设中）</div>
</template>
<script setup></script>
<style scoped>
.request-module { flex: 1; padding: 24px; }
</style>
```

- [ ] **Step 3: 改写 App.vue 为模块外壳**

`frontend/src/App.vue`：
```vue
<template>
  <div class="app">
    <header class="global-nav">
      <span class="nav-title">个人工作空间站</span>
      <nav class="module-tabs">
        <button
          v-for="m in modules"
          :key="m.key"
          class="module-tab"
          :class="{ active: activeModule === m.key }"
          @click="activeModule = m.key"
        >{{ m.label }}</button>
      </nav>
    </header>
    <div class="app-body">
      <ViewerModule v-show="activeModule === 'viewer'" />
      <RequestModule v-show="activeModule === 'request'" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ViewerModule from './modules/ViewerModule.vue'
import RequestModule from './modules/RequestModule.vue'

const modules = [
  { key: 'viewer', label: '数据查看器' },
  { key: 'request', label: '请求工具' },
]
const activeModule = ref('viewer')
</script>

<style scoped>
.app { display: flex; flex-direction: column; height: 100vh; }
.global-nav {
  display: flex; align-items: center; gap: 24px;
  padding: 0 20px; height: 48px; flex-shrink: 0;
  border-bottom: 1px solid rgba(0,0,0,0.08);
  background: rgba(255,255,255,0.8); backdrop-filter: blur(20px);
}
.nav-title { font-weight: 600; font-size: 15px; }
.module-tabs { display: flex; gap: 4px; }
.module-tab {
  border: none; background: none; cursor: pointer;
  padding: 6px 14px; border-radius: 8px; font-size: 14px; color: #555;
}
.module-tab.active { background: rgba(0,122,255,0.12); color: #007aff; font-weight: 600; }
.app-body { flex: 1; display: flex; min-height: 0; }
</style>
```
> 注：用 `v-show` 而非 `v-if`，保留各模块状态（切换 Tab 不丢失已加载的文件树/请求草稿）。

- [ ] **Step 4: 构建验证**

Run: `cd frontend && npm run build`
Expected: 构建成功，无报错。

- [ ] **Step 5: 手动验证**

启动后端 `python main.py --port 8002` 与前端 `cd frontend && npm run dev`，打开页面：顶部出现「数据查看器 / 请求工具」两个 Tab，查看器功能（扫描、选文件、另存为）与改造前一致；点「请求工具」显示占位文案。

- [ ] **Step 6: 提交**

```bash
git add frontend/src/App.vue frontend/src/modules/ViewerModule.vue frontend/src/modules/RequestModule.vue
git commit -m "feat: 顶部 Tab 模块导航 + 查看器模块抽取"
```

---

## Task 9: KeyValueEditor 组件

**Files:**
- Create: `frontend/src/components/request/KeyValueEditor.vue`

- [ ] **Step 1: 实现组件**

`frontend/src/components/request/KeyValueEditor.vue`：
```vue
<template>
  <div class="kv-editor">
    <div v-for="(row, idx) in rows" :key="idx" class="kv-row">
      <el-checkbox v-model="row.enabled" @change="emitChange" />
      <el-input v-model="row.key" placeholder="Key" size="small" @input="emitChange" />
      <el-input v-model="row.value" placeholder="Value" size="small" @input="emitChange" />
      <button class="kv-del" @click="removeRow(idx)">✕</button>
    </div>
    <button class="kv-add" @click="addRow">+ 添加一行</button>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({ modelValue: { type: Array, default: () => [] } })
const emit = defineEmits(['update:modelValue'])

const rows = ref(props.modelValue.map((r) => ({ ...r })))

watch(
  () => props.modelValue,
  (val) => {
    // 仅在外部数据与当前不同步时重建（避免编辑光标丢失）
    if (JSON.stringify(val) !== JSON.stringify(rows.value)) {
      rows.value = (val || []).map((r) => ({ ...r }))
    }
  }
)

function addRow() {
  rows.value.push({ key: '', value: '', enabled: true })
  emitChange()
}
function removeRow(i) {
  rows.value.splice(i, 1)
  emitChange()
}
function emitChange() {
  emit('update:modelValue', rows.value.map((r) => ({ ...r })))
}
</script>

<style scoped>
.kv-editor { display: flex; flex-direction: column; gap: 8px; padding: 8px 0; }
.kv-row { display: flex; align-items: center; gap: 8px; }
.kv-del { border: none; background: none; color: #999; cursor: pointer; }
.kv-del:hover { color: #ff3b30; }
.kv-add { align-self: flex-start; border: none; background: none; color: #007aff; cursor: pointer; font-size: 13px; }
</style>
```

- [ ] **Step 2: 构建验证**

Run: `cd frontend && npm run build`
Expected: 构建成功。

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/request/KeyValueEditor.vue
git commit -m "feat: KeyValueEditor 键值对编辑器"
```

---

## Task 10: BodyEditor 组件

**Files:**
- Create: `frontend/src/components/request/BodyEditor.vue`

- [ ] **Step 1: 实现组件**

`frontend/src/components/request/BodyEditor.vue`：
```vue
<template>
  <div class="body-editor">
    <el-radio-group :model-value="bodyType" size="small" @change="onTypeChange">
      <el-radio-button value="none">none</el-radio-button>
      <el-radio-button value="json">JSON</el-radio-button>
      <el-radio-button value="raw">raw</el-radio-button>
      <el-radio-button value="form">form</el-radio-button>
    </el-radio-group>

    <div v-if="bodyType === 'json' || bodyType === 'raw'" class="body-text">
      <el-input
        :model-value="body"
        type="textarea"
        :rows="10"
        :placeholder="bodyType === 'json' ? 'JSON 请求体，例如 {"key": "value"}' : '原始请求体'"
        @input="(v) => emit('update:body', v)"
      />
    </div>

    <div v-else-if="bodyType === 'form'" class="body-form">
      <KeyValueEditor :model-value="formBody" @update:model-value="(v) => emit('update:formBody', v)" />
    </div>
  </div>
</template>

<script setup>
import KeyValueEditor from './KeyValueEditor.vue'

defineProps({
  bodyType: { type: String, default: 'none' },
  body: { type: String, default: '' },
  formBody: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:bodyType', 'update:body', 'update:formBody'])

function onTypeChange(v) {
  emit('update:bodyType', v)
}
</script>

<style scoped>
.body-editor { display: flex; flex-direction: column; gap: 12px; padding: 8px 0; }
.body-text :deep(textarea) { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px; }
</style>
```

- [ ] **Step 2: 构建验证**

Run: `cd frontend && npm run build`
Expected: 构建成功。

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/request/BodyEditor.vue
git commit -m "feat: BodyEditor 请求体编辑器"
```

---

## Task 11: ResponseView 组件

**Files:**
- Create: `frontend/src/components/request/ResponseView.vue`

- [ ] **Step 1: 实现组件**

`frontend/src/components/request/ResponseView.vue`：
```vue
<template>
  <div class="response-view">
    <div v-if="loading" class="resp-placeholder">发送中…</div>
    <div v-else-if="!response" class="resp-placeholder">点「发送」查看响应</div>
    <div v-else-if="response.error" class="resp-error">请求失败：{{ response.error }}</div>
    <template v-else>
      <div class="resp-statusbar">
        <span class="status-code" :class="statusClass">{{ response.status }} {{ response.status_text }}</span>
        <span class="resp-meta">{{ response.elapsed_ms }} ms</span>
        <span class="resp-meta">{{ prettySize }}</span>
        <span v-if="response.truncated" class="resp-meta warn">响应体过大，已截断</span>
      </div>
      <el-tabs v-model="activeTab" class="resp-tabs">
        <el-tab-pane label="Body" name="body">
          <pre class="resp-body">{{ prettyBody }}</pre>
        </el-tab-pane>
        <el-tab-pane label="Headers" name="headers">
          <div v-for="(v, k) in response.headers" :key="k" class="resp-header-row">
            <span class="hk">{{ k }}</span><span class="hv">{{ v }}</span>
          </div>
        </el-tab-pane>
      </el-tabs>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  response: { type: Object, default: null },
  loading: { type: Boolean, default: false },
})
const activeTab = ref('body')

const statusClass = computed(() => {
  const s = props.response?.status || 0
  if (s >= 200 && s < 300) return 'ok'
  if (s >= 400) return 'err'
  return 'other'
})

const prettySize = computed(() => {
  const n = props.response?.size_bytes || 0
  if (n < 1024) return n + ' B'
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB'
  return (n / 1024 / 1024).toFixed(2) + ' MB'
})

const prettyBody = computed(() => {
  const body = props.response?.body || ''
  const ct = props.response?.content_type || ''
  if (ct.includes('json')) {
    try {
      return JSON.stringify(JSON.parse(body), null, 2)
    } catch {
      return body
    }
  }
  return body
})
</script>

<style scoped>
.response-view { display: flex; flex-direction: column; min-height: 0; }
.resp-placeholder { padding: 24px; color: #999; }
.resp-error { padding: 16px; color: #ff3b30; }
.resp-statusbar { display: flex; align-items: center; gap: 16px; padding: 10px 4px; font-size: 13px; }
.status-code { font-weight: 600; }
.status-code.ok { color: #34c759; }
.status-code.err { color: #ff3b30; }
.status-code.other { color: #ff9500; }
.resp-meta { color: #888; }
.resp-meta.warn { color: #ff9500; }
.resp-body {
  margin: 0; padding: 12px; background: #f6f6f8; border-radius: 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px;
  white-space: pre-wrap; word-break: break-all; max-height: 50vh; overflow: auto;
}
.resp-header-row { display: flex; gap: 12px; padding: 4px 0; font-size: 13px; }
.hk { color: #007aff; min-width: 200px; }
.hv { color: #333; word-break: break-all; }
</style>
```

- [ ] **Step 2: 构建验证**

Run: `cd frontend && npm run build`
Expected: 构建成功。

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/request/ResponseView.vue
git commit -m "feat: ResponseView 响应展示"
```

---

## Task 12: CurlImportDialog 组件

**Files:**
- Create: `frontend/src/components/request/CurlImportDialog.vue`

- [ ] **Step 1: 实现组件**

`frontend/src/components/request/CurlImportDialog.vue`：
```vue
<template>
  <el-dialog :model-value="modelValue" title="导入 curl" width="600px"
             @update:model-value="(v) => emit('update:modelValue', v)">
    <el-input v-model="text" type="textarea" :rows="8" placeholder="粘贴 curl 命令…" />
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="loading" @click="doImport">导入</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { parseCurl } from '../../api'

defineProps({ modelValue: { type: Boolean, default: false } })
const emit = defineEmits(['update:modelValue', 'imported'])

const text = ref('')
const loading = ref(false)

async function doImport() {
  if (!text.value.trim()) {
    ElMessage.warning('请粘贴 curl 命令')
    return
  }
  loading.value = true
  try {
    const { data } = await parseCurl(text.value)
    emit('imported', data)
    emit('update:modelValue', false)
    text.value = ''
  } catch (e) {
    ElMessage.error('解析失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}
</script>
```

- [ ] **Step 2: 构建验证**

Run: `cd frontend && npm run build`
Expected: 构建成功。

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/request/CurlImportDialog.vue
git commit -m "feat: CurlImportDialog 导入弹窗"
```

---

## Task 13: SampleList 组件

**Files:**
- Create: `frontend/src/components/request/SampleList.vue`

- [ ] **Step 1: 实现组件**

`frontend/src/components/request/SampleList.vue`：
```vue
<template>
  <div class="sample-list">
    <div class="sl-header">
      <span>请求样例</span>
    </div>
    <div v-if="!samples.length" class="sl-empty">暂无样例</div>
    <div
      v-for="s in samples"
      :key="s.id"
      class="sl-item"
      :class="{ active: s.id === activeId }"
      @click="emit('load', s)"
    >
      <span class="sl-method" :data-m="s.request.method">{{ s.request.method }}</span>
      <span class="sl-name">{{ s.name }}</span>
      <span class="sl-actions">
        <button class="sl-btn" @click.stop="rename(s)">改名</button>
        <button class="sl-btn del" @click.stop="emit('delete', s.id)">删</button>
      </span>
    </div>
  </div>
</template>

<script setup>
import { ElMessageBox } from 'element-plus'

defineProps({
  samples: { type: Array, default: () => [] },
  activeId: { type: String, default: '' },
})
const emit = defineEmits(['load', 'delete', 'rename'])

async function rename(s) {
  try {
    const { value } = await ElMessageBox.prompt('新名称', '重命名', { inputValue: s.name })
    if (value && value.trim()) emit('rename', { id: s.id, name: value.trim() })
  } catch (e) { /* 取消 */ }
}
</script>

<style scoped>
.sample-list { display: flex; flex-direction: column; }
.sl-header { padding: 12px 14px; font-weight: 600; font-size: 13px; color: #555; }
.sl-empty { padding: 12px 14px; color: #aaa; font-size: 13px; }
.sl-item {
  display: flex; align-items: center; gap: 8px; padding: 10px 14px;
  cursor: pointer; border-radius: 8px; margin: 0 6px;
}
.sl-item:hover { background: rgba(0,122,255,0.06); }
.sl-item.active { background: rgba(0,122,255,0.12); }
.sl-method { font-size: 11px; font-weight: 700; color: #007aff; min-width: 38px; }
.sl-name { flex: 1; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sl-actions { display: none; gap: 6px; }
.sl-item:hover .sl-actions { display: flex; }
.sl-btn { border: none; background: none; color: #888; cursor: pointer; font-size: 12px; }
.sl-btn.del:hover { color: #ff3b30; }
</style>
```

- [ ] **Step 2: 构建验证**

Run: `cd frontend && npm run build`
Expected: 构建成功。

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/request/SampleList.vue
git commit -m "feat: SampleList 样例列表"
```

---

## Task 14: RequestBuilder + RequestModule 集成（含草稿自动保存）

**Files:**
- Create: `frontend/src/components/request/RequestBuilder.vue`
- Modify: `frontend/src/modules/RequestModule.vue`

- [ ] **Step 1: 实现 RequestBuilder**

`frontend/src/components/request/RequestBuilder.vue`：
```vue
<template>
  <div class="request-builder">
    <div class="rb-line">
      <el-select :model-value="spec.method" style="width: 110px"
                 @change="(v) => update('method', v)">
        <el-option v-for="m in methods" :key="m" :label="m" :value="m" />
      </el-select>
      <el-input :model-value="spec.url" placeholder="请求 URL" class="rb-url"
                @input="(v) => update('url', v)" />
      <el-button type="primary" :loading="loading" @click="emit('send')">发送</el-button>
    </div>
    <div class="rb-tools">
      <button class="rb-tool" @click="emit('import-curl')">导入 curl</button>
      <button class="rb-tool" @click="emit('copy-curl')">复制为 curl</button>
      <button class="rb-tool" @click="emit('save-as')">另存为样例</button>
      <button class="rb-tool" v-if="canUpdate" @click="emit('update-sample')">更新当前样例</button>
    </div>

    <el-tabs v-model="activeTab" class="rb-tabs">
      <el-tab-pane label="Params" name="params">
        <KeyValueEditor :model-value="spec.params" @update:model-value="(v) => update('params', v)" />
      </el-tab-pane>
      <el-tab-pane label="Headers" name="headers">
        <KeyValueEditor :model-value="spec.headers" @update:model-value="(v) => update('headers', v)" />
      </el-tab-pane>
      <el-tab-pane label="Body" name="body">
        <BodyEditor
          :body-type="spec.body_type" :body="spec.body" :form-body="spec.form_body"
          @update:body-type="(v) => update('body_type', v)"
          @update:body="(v) => update('body', v)"
          @update:form-body="(v) => update('form_body', v)"
        />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import KeyValueEditor from './KeyValueEditor.vue'
import BodyEditor from './BodyEditor.vue'

const props = defineProps({
  spec: { type: Object, required: true },
  loading: { type: Boolean, default: false },
  canUpdate: { type: Boolean, default: false },
})
const emit = defineEmits(['update:spec', 'send', 'import-curl', 'copy-curl', 'save-as', 'update-sample'])

const methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']
const activeTab = ref('params')

function update(key, value) {
  emit('update:spec', { ...props.spec, [key]: value })
}
</script>

<style scoped>
.request-builder { display: flex; flex-direction: column; gap: 12px; }
.rb-line { display: flex; gap: 8px; }
.rb-url { flex: 1; }
.rb-tools { display: flex; gap: 14px; }
.rb-tool { border: none; background: none; color: #007aff; cursor: pointer; font-size: 13px; }
</style>
```

- [ ] **Step 2: 实现 RequestModule（左右布局 + 草稿自动保存 + 样例操作）**

`frontend/src/modules/RequestModule.vue`：
```vue
<template>
  <div class="request-module">
    <aside class="rm-sidebar">
      <SampleList
        :samples="store.samples" :active-id="activeId"
        @load="loadSample" @delete="deleteSample" @rename="renameSample"
      />
    </aside>
    <main class="rm-main">
      <RequestBuilder
        :spec="spec" :loading="sending" :can-update="!!activeId"
        @update:spec="onSpecChange"
        @send="send"
        @import-curl="showImport = true"
        @copy-curl="copyCurl"
        @save-as="saveAsSample"
        @update-sample="updateSample"
      />
      <ResponseView :response="response" :loading="sending" />
    </main>

    <CurlImportDialog v-model="showImport" @imported="onCurlImported" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import SampleList from '../components/request/SampleList.vue'
import RequestBuilder from '../components/request/RequestBuilder.vue'
import ResponseView from '../components/request/ResponseView.vue'
import CurlImportDialog from '../components/request/CurlImportDialog.vue'
import { sendRequest, toCurl, getRequestSamples, saveRequestSamples } from '../api'

function emptySpec() {
  return { method: 'GET', url: '', params: [], headers: [], body_type: 'none', body: '', form_body: [] }
}

const store = ref({ samples: [], draft: null })
const spec = ref(emptySpec())
const activeId = ref('')
const response = ref(null)
const sending = ref(false)
const showImport = ref(false)

let saveTimer = null

onMounted(async () => {
  try {
    const { data } = await getRequestSamples()
    store.value = { samples: data.samples || [], draft: data.draft || null }
    if (store.value.draft) spec.value = { ...emptySpec(), ...store.value.draft }
  } catch (e) {
    ElMessage.error('加载样例失败：' + e.message)
  }
})

function persist() {
  return saveRequestSamples({ samples: store.value.samples, draft: spec.value })
}

function scheduleDraftSave() {
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => persist().catch(() => {}), 500)
}

function onSpecChange(next) {
  spec.value = next
  scheduleDraftSave()
}

async function send() {
  sending.value = true
  response.value = null
  try {
    const { data } = await sendRequest(spec.value)
    response.value = data
  } catch (e) {
    response.value = { error: e.response?.data?.detail || e.message }
  } finally {
    sending.value = false
  }
}

async function copyCurl() {
  try {
    const { data } = await toCurl(spec.value)
    await navigator.clipboard.writeText(data.curl)
    ElMessage.success('已复制 curl 到剪贴板')
  } catch (e) {
    ElMessage.error('复制失败：' + e.message)
  }
}

function onCurlImported(parsed) {
  spec.value = { ...emptySpec(), ...parsed }
  activeId.value = ''
  scheduleDraftSave()
  ElMessage.success('已导入 curl')
}

function loadSample(s) {
  activeId.value = s.id
  spec.value = { ...emptySpec(), ...s.request }
  scheduleDraftSave()
}

async function saveAsSample() {
  try {
    const { value } = await ElMessageBox.prompt('样例名称', '另存为样例')
    if (!value || !value.trim()) return
    const id = String(Date.now())
    store.value.samples.push({ id, name: value.trim(), request: spec.value })
    activeId.value = id
    await persist()
    ElMessage.success('已保存样例')
  } catch (e) { /* 取消 */ }
}

async function updateSample() {
  const target = store.value.samples.find((s) => s.id === activeId.value)
  if (!target) return
  target.request = spec.value
  await persist()
  ElMessage.success('已更新样例')
}

function renameSample({ id, name }) {
  const target = store.value.samples.find((s) => s.id === id)
  if (target) { target.name = name; persist() }
}

async function deleteSample(id) {
  store.value.samples = store.value.samples.filter((s) => s.id !== id)
  if (activeId.value === id) activeId.value = ''
  await persist()
}
</script>

<style scoped>
.request-module { display: flex; flex: 1; min-height: 0; }
.rm-sidebar { width: 260px; flex-shrink: 0; overflow: auto; border-right: 1px solid rgba(0,0,0,0.08); }
.rm-main { flex: 1; min-width: 0; overflow: auto; padding: 20px; display: flex; flex-direction: column; gap: 20px; }
</style>
```

- [ ] **Step 3: 构建验证**

Run: `cd frontend && npm run build`
Expected: 构建成功，无报错。

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/request/RequestBuilder.vue frontend/src/modules/RequestModule.vue
git commit -m "feat: RequestBuilder 与 RequestModule 集成"
```

---

## Task 15: 端到端手动验证

**Files:** 无（仅验证）

- [ ] **Step 1: 启动**

后端：`python main.py --port 8002`
前端：`cd frontend && npm run dev`

- [ ] **Step 2: 逐项验证清单**

- [ ] 顶部切到「请求工具」，左侧样例区显示「暂无样例」
- [ ] 填 `GET https://httpbin.org/get`，加一个 Param `q=hi`，点发送 → 状态码 200，Body 格式化 JSON，能看到 `args.q=hi`，耗时/大小正常
- [ ] Headers 加一行 `X-Test: 1`，发送 → httpbin 回显里含该 header
- [ ] 切到 Body→JSON，method 改 POST，URL `https://httpbin.org/post`，填 `{"a":1}`，发送 → 200 且回显 json
- [ ] 点「复制为 curl」→ 提示已复制，粘贴到终端能正常执行
- [ ] 点「导入 curl」，粘贴 `curl -X POST https://httpbin.org/post -H 'Content-Type: application/json' --data-raw '{"b":2}'` → 面板被正确填充
- [ ] 点「另存为样例」命名「测试」→ 左侧出现该样例
- [ ] 刷新页面 → 仍在请求工具？（注：Tab 默认回 viewer，切到请求工具）样例仍在；上次编辑的请求草稿被恢复
- [ ] 改动当前样例的 URL，点「更新当前样例」→ 重新载入该样例确认已更新
- [ ] 样例「改名」「删」均生效
- [ ] 故意填一个打不通的地址（如 `http://127.0.0.1:1`）发送 → 响应区显示「请求失败：…」而非崩溃
- [ ] 切回「数据查看器」，原有功能完全正常

- [ ] **Step 3: 后端全量回归**

Run: `python -m pytest tests/ -v`
Expected: 全部 PASS

- [ ] **Step 4: 最终提交（如有手动验证中的小修）**

```bash
git add -A
git commit -m "test: 请求工具端到端验证与修整"
```

---

## 验收标准

- 后端 4 个新测试文件全部通过，原有测试不回归
- 前端 `npm run build` 通过
- 手动验证清单全部勾选
- 两个模块互不干扰，切换不丢状态
