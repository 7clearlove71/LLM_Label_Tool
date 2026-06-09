# 请求工具设计方案（功能二 / v1 MVP）

日期：2026-06-09
状态：已确认，待实现

## 背景与定位

本项目从「LLM 训练数据查看器」升级为**个人工作空间站**，承载多个相互独立的本地工具。

- 功能一：现有的 JSON/JSONL 数据查看器
- 功能二（本文档）：类似 Postman 的 HTTP 请求发送/调试工具

工作空间站后续还会扩展功能三、功能四，因此本次需引入一层模块导航，并保证新功能与现有结构、风格一致。

## 目标（v1 范围）

精简档 MVP，单请求面板，核心能力：

- 选择 method、填写 URL、Query 参数、Headers、Body（none/json/raw/form）
- 后端代理发送请求，展示响应（状态码、耗时、大小、响应头、格式化响应体）
- 左侧保存请求样例（扁平列表），可载入、重命名、删除、另存为、更新覆盖
- 自动记住面板最后一次编辑的请求状态（草稿），重开工具时恢复
- 粘贴 curl 导入（解析为结构化请求）
- 当前请求一键导出为 curl 命令并复制

## 非目标（v1 明确不做，按数据结构预留但不实现）

- 样例分组/文件夹（Collection）
- 请求历史记录
- 环境变量与多环境切换（`{{base_url}}`）
- 认证助手（Bearer/Basic 一键填充）
- 多标签页同时编辑多个请求
- 保存样例时附带响应快照（样例只存请求模板）
- 样例数量上限（不限制）

## 关键决策

| 决策点 | 选择 | 理由 |
| --- | --- | --- |
| 谁发出 HTTP 请求 | **后端代理**（httpx） | 无浏览器 CORS 限制、可打内网/localhost、可设任意 header、可拿全量响应头；`httpx` 已在依赖中 |
| 模块导航形态 | **顶部 Tab 切换**（响应式 `activeModule`，不引 vue-router） | 改动最小，本地工具无需可分享 URL |
| curl 解析/生成位置 | **后端** | Python 解析更稳，与发送同侧；可写单测；导入/导出对称 |
| 样例持久化 | **json 文件 `requests.json`** | 沿用现有 `bookmarks.json` 模式，无需引入数据库 |
| 草稿持久化 | 与样例同文件，面板编辑防抖自动保存 | 实现「记住最后一次编辑状态」 |

## 架构

### 模块导航

- `App.vue` 顶栏新增 Tab：**数据查看器 / 请求工具**，由响应式状态 `activeModule` 控制主区域渲染。
- 将现有「文件树侧边栏 + DataView + 另存为」逻辑抽取为 `modules/ViewerModule.vue`，保持现有行为不变。
- 新建 `modules/RequestModule.vue` 承载请求工具。两个模块各自管理自己的内部侧边栏。

### 后端

新增路由 `backend/routers/request.py`，在 `backend/app.py` 中 `include_router`。配套三个 service：

| 接口 | 方法 | service | 说明 |
| --- | --- | --- | --- |
| `/api/request/send` | POST | `services/http_client.py` | 接收 RequestSpec，用 httpx 发出，返回 ResponseResult |
| `/api/request/parse-curl` | POST | `services/curl_parser.py` | 整段 curl 文本 → RequestSpec |
| `/api/request/to-curl` | POST | `services/curl_parser.py` | RequestSpec → curl 命令字符串 |
| `/api/requests` | GET | `services/request_store.py` | 读取 `{samples, draft}` |
| `/api/requests` | PUT | `services/request_store.py` | 写入 `{samples, draft}` |

### 前端

```
frontend/src/
  modules/
    ViewerModule.vue        # 现有查看器抽取
    RequestModule.vue       # 左右布局：左=样例列表，右=请求构建+响应
  components/request/
    SampleList.vue          # 样例增删改、载入、另存为、更新覆盖
    RequestBuilder.vue      # method 下拉 + URL + 发送 + 导入curl + 复制为curl；Tab: Params/Headers/Body
    KeyValueEditor.vue      # Params 与 Headers 复用的键值对编辑器（每行可启用/禁用）
    BodyEditor.vue          # body 类型选择 + 编辑（JSON 复用已有格式化）
    ResponseView.vue        # 状态条（状态码/耗时/大小）+ Tab: Body/Headers
    CurlImportDialog.vue    # 粘贴 curl 弹窗
  api/index.js              # 新增 sendRequest/parseCurl/toCurl/getRequestSamples/saveRequestSamples
```

## 数据模型（`backend/models.py`）

```python
class KeyValueItem(BaseModel):
    key: str
    value: str
    enabled: bool = True

class RequestSpec(BaseModel):
    method: str = "GET"          # GET/POST/PUT/PATCH/DELETE/...
    url: str = ""
    params: list[KeyValueItem] = []
    headers: list[KeyValueItem] = []
    body_type: str = "none"      # none | json | raw | form
    body: str = ""               # json/raw 类型的文本内容
    form_body: list[KeyValueItem] = []  # form 类型时的键值对，body 留空

class ResponseResult(BaseModel):
    status: int | None = None
    status_text: str = ""
    elapsed_ms: float = 0
    size_bytes: int = 0
    headers: dict[str, str] = {}
    content_type: str = ""
    body: str = ""
    error: str | None = None     # 网络层错误时填充，status 为 None

class RequestSample(BaseModel):
    id: str
    name: str
    request: RequestSpec

class RequestStore(BaseModel):
    samples: list[RequestSample] = []
    draft: RequestSpec | None = None
```

`requests.json` 结构：

```json
{ "samples": [ { "id": "...", "name": "...", "request": { } } ], "draft": { } }
```

## 数据流

1. 进入请求工具 → `GET /api/requests` → 填充样例列表 + 恢复草稿到面板。
2. 面板编辑 → 防抖（~500ms）`PUT /api/requests`，更新 `draft`，实现「记住最后一次编辑状态」。
3. 点发送 → `POST /api/request/send` → 渲染 ResponseView。
4. 另存为新样例 / 更新当前样例 → 修改 `samples` → `PUT /api/requests`。
5. 导入 curl → 弹窗粘贴 → `POST /api/request/parse-curl` → 回填面板。
6. 复制为 curl → `POST /api/request/to-curl` → 写入剪贴板。

## 错误处理

- httpx 的超时 / 连接失败 / DNS 解析失败 **不抛 500**，统一捕获后以 `ResponseResult.error` 返回，`status=None`，前端在响应区展示错误信息。
- 发送超时默认 30s。
- 非文本响应（图片/二进制，依 `content_type` 判断）：仅显示大小和类型，不强行渲染。
- 超大文本响应（>2MB）：截断展示并提示。
- curl 解析失败：返回明确错误信息，前端弹窗内提示，不回填。

## 样式

沿用现有 Apple 风格（圆角卡片、hairline 边框、蓝色激活态、Apple 字体），与数据查看器视觉统一。复用现有 Element Plus 与自定义样式约定。

## 测试（`tests/`，沿用现有 pytest 风格）

- **curl 解析器**：覆盖 `-X` / 多个 `-H` / `-d`/`--data`/`--data-raw` / `--url` / 带与不带 `curl` 前缀 / 多行 `\` 续行。
- **curl 导入/导出往返**：RequestSpec → curl → RequestSpec 一致性。
- **request_store**：json 读写、样例增删改、草稿存取、文件不存在时返回空 store。
- **send 接口**：用 httpx `MockTransport` 验证状态码/响应头透传、耗时与大小、网络错误被捕获为 `error` 而非 500。
