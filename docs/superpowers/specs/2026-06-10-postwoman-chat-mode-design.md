# postwoman 对话框模式 — 设计文档

日期：2026-06-10
状态：已确认，待实现

## 1. 背景与目标

postwoman（Postman-lite）当前是通用 HTTP 请求工具：一条样例 = 一条 `RequestSpec`，
后端用 httpx **同步、非流式**发送，前端 `RequestBuilder` 编辑、`ResponseView` 展示。
没有任何「对话 / 消息」概念。

本次升级：让一条指向 **LLM chat 接口**的请求，能在「请求编辑视图」与「对话视图」之间双向切换。
对话视图仿 Claude 官网：多轮对话、reasoning 可折叠、保存/删除历史对话、回复流式逐字输出。

### 已确认决策

| 项 | 决策 |
| --- | --- |
| 接口格式 | **OpenAI 兼容**（`/chat/completions`，`messages:[{role,content}]`，reasoning 走 `reasoning_content`） |
| 回复方式 | **流式 SSE**（`stream:true`） |
| 对话归属 | **每个样例多个对话**（样例 = API 配置，对话挂在样例下） |
| 状态共享 | **方案 B：模板 + 消息分离** |
| reasoning 折叠 | **流式时展开、完成后自动折叠**，可手动展开 |
| 实现节奏 | **直接上流式**，不做非流式过渡版 |

### v1 不做（YAGNI）

消息中途编辑/分支重发、多模型对比、token 计费、非流式回退、Anthropic Messages 格式。

## 2. 数据模型

后端 `backend/models.py` 扩展：

```python
class Message(BaseModel):
    role: Literal["system", "user", "assistant"] = "user"
    content: str = ""
    reasoning: str = ""              # reasoning_content，可折叠

class Conversation(BaseModel):
    id: str
    name: str = "新对话"
    messages: list[Message] = []
    created_at: str = ""
    updated_at: str = ""

class RequestSample(BaseModel):
    id: str
    name: str
    request: RequestSpec             # 模板：body 里除 messages 外的 API 配置
    mode: Literal["request", "chat"] = "request"   # 该样例上次所在视图
    conversations: list[Conversation] = []
    active_conversation_id: Optional[str] = None
```

- **模板** = `request.body` 里除 `messages` 外的 API 配置（model、temperature、url、headers、`stream` 等）。
- **对话** = 只存自己的完整 `messages`（含 system）。
- 兼容性：旧 `requests.json` 缺新字段，靠 pydantic 默认值平滑兼容，**无需迁移脚本**。
  `request_store.py` 的原子写不变。

## 3. 视图切换语义（双向无损）

切换是同一份数据的两种渲染，`mode` 字段记在样例上。

- **请求编辑 → 对话**：解析 `request.body` 的 JSON，抽出 `messages` 渲染为气泡。
  解析失败（body 非合法 JSON）→ 提示「当前 body 不是合法 JSON，无法转为对话」，留在编辑视图。
- **对话 → 请求编辑**：把「模板配置 + 当前对话的 messages」**拼接成完整 body** 回填编辑视图。
  这就是「自动拼接多轮请求」，可直接复制为 curl。
- **改模板配置**（model/url/headers/采样参数）→ 对该样例**所有对话**生效。
- **改 messages** → 只改**当前对话**。切换对话只换 messages，配置不漂移。

### 请求装配（发送时）

```
merged_body = { ...parse(template.body 去掉 messages),
                messages: [{role, content} for m in conversation.messages],
                stream: true }
```

在前端装配，POST 到流式端点。`reasoning` 字段不回传给上游（仅本地展示）。

## 4. 后端流式转发

新增 `backend/services/chat_stream.py` + 路由 `POST /api/request/chat/stream`：

- 接收装配好的请求 spec（method=POST、url、headers、含 `stream:true` 的 body）。
- 用 `httpx.stream("POST", ...)` 连接目标 LLM，逐行读上游 SSE 的 `data:` 行。
- 解析每行 JSON，从 `choices[0].delta` 取 `content` 与 reasoning。
  - **reasoning 字段兼容**：依次取 `delta.reasoning_content`（DeepSeek/vLLM 等）→ `delta.reasoning`（OpenRouter 等），
    取到第一个非空即用。两者归一为转发事件里的 `reasoning` 字段。
- 以 **SSE 事件**重新转发给前端：
  - `event: delta`，data = `{ "content": "...", "reasoning": "..." }`（增量，可只含其一）
  - `event: done`，data = `{}`（上游发 `data: [DONE]` 时）
  - `event: error`，data = `{ "message": "..." }`
- 用 FastAPI `StreamingResponse(media_type="text/event-stream")`。
- 同步 `http_client.py` 保留给普通（非对话）请求。

### 错误处理

| 情况 | 行为 |
| --- | --- |
| 上游非 2xx | 读取错误体 → 发 `error` 事件 |
| 上游非 SSE / 解析失败 | 发 `error` 事件，附原始片段 |
| 网络中断 / 超时 | 发 `error` 事件 |
| 前端收到 `error` | 显示错误气泡，**不追加**残缺 assistant 消息 |

### 测试

`tests/` 新增对「上游 SSE 分片 → 转发事件」转换逻辑的 pytest 单测（仿 `curl_parser` 风格）：
正常分片、reasoning 与 content 混合、`reasoning_content` 与 `reasoning` 两种字段、`[DONE]`、坏行跳过、上游错误。

## 5. 前端组件与交互（仿 Claude 网页）

### 新组件

- **`ChatView.vue`** — 对话主体：消息气泡列表 + 底部输入框 + 发送/停止按钮。
  用 `fetch` + `ReadableStream` reader 读流（EventSource 不支持 POST body），逐字渲染。
  停止生成 = `AbortController.abort()`，已生成部分保留并入库。
- **`MessageBubble.vue`** — user / assistant 气泡。assistant 的 reasoning 用可折叠块「思考过程」：
  **流式时展开 → 完成后自动折叠**，可手动展开。
- **`ConversationList.vue`** — 当前样例的对话列表：新建 / 切换 / 重命名 / 删除某条历史对话。
  在对话视图内（侧栏二级面板或顶部）。

### 改动

- **`RequestModule.vue`** — 加 `mode` 切换、对话与 active_conversation 状态、装配/解析、
  流式编排、持久化（每轮完成后落库，复用现有原子写 + 串行 persist 链）。
- **`RequestBuilder.vue`** — 顶部加「请求 / 对话」切换开关；编辑视图 body 反映拼接结果。
- **`api/index.js`** — 加流式对话调用封装（fetch + reader）。

### 流式交互流程

1. 用户在输入框输入 → 追加一条 user message 到当前对话。
2. 前端装配 body（§3）→ `fetch` 流式端点。
3. 创建一条空 assistant message，随 `delta` 事件逐字填 `content` / `reasoning`。
4. `done` → 自动折叠 reasoning，整段落库（持久化对话）。
5. `error` → 显示错误气泡，回滚未完成的 assistant message。
6. 用户可点「停止」中断；已生成内容保留入库。

## 6. 组件边界小结

| 单元 | 职责 | 依赖 |
| --- | --- | --- |
| `chat_stream.py` | 连接上游 LLM、转发 SSE 事件 | httpx |
| `/api/request/chat/stream` | 路由，包装 StreamingResponse | chat_stream |
| `ChatView.vue` | 读流、渲染对话、输入/发送/停止 | api、MessageBubble |
| `MessageBubble.vue` | 单条气泡 + reasoning 折叠 | — |
| `ConversationList.vue` | 对话增删改查切换 | — |
| `RequestModule.vue` | 模式切换、装配/解析、状态与持久化编排 | 上述全部 |

每个单元单一职责、接口清晰，可独立理解与测试。
