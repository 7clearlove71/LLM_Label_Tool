# postwoman 对话框模式 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给 postwoman 增加「请求编辑 ↔ 对话框」双向切换，对话框仿 Claude 网页：多轮、reasoning 可折叠、流式输出、每样例多对话可存/删。

**Architecture:** 方案 B（模板+消息分离）。样例 `request` 是 API 配置模板，对话只存 `messages`。后端新增 `chat_stream.py` 把上游 OpenAI 兼容 SSE 转发为前端 SSE；前端 `fetch`+`ReadableStream` 逐字渲染。切换视图时在「模板 body」与「对话 messages」间双向同步。

**Tech Stack:** FastAPI + httpx streaming（后端）；Vue 3 + Element Plus + fetch streaming（前端）。后端用 pytest TDD；前端无 JS 测试框架，用浏览器手动验证。

参考 spec：`docs/superpowers/specs/2026-06-10-postwoman-chat-mode-design.md`

---

## 文件结构

**后端**
- 修改 `backend/models.py` — 新增 `Message` / `Conversation`，扩展 `RequestSample`。
- 新建 `backend/services/chat_stream.py` — 纯函数 `transform_sse_lines` / `format_sse` + 流式运行器 `stream_chat`。
- 修改 `backend/routers/request.py` — 新增 `POST /api/request/chat/stream` 路由。
- 新建 `tests/test_chat_stream.py` — SSE 转换单测。
- 修改 `tests/test_request_models.py` — 新模型默认值测试。

**前端**
- 修改 `frontend/src/api/index.js` — 新增 `chatStream` fetch 流式封装。
- 新建 `frontend/src/components/request/MessageBubble.vue` — 单条气泡 + reasoning 折叠。
- 新建 `frontend/src/components/request/ChatView.vue` — 对话主体（渲染/输入/发送/停止/读流）。
- 新建 `frontend/src/components/request/ConversationList.vue` — 对话增删改查切换。
- 修改 `frontend/src/components/request/RequestBuilder.vue` — 顶部「请求/对话」切换开关。
- 修改 `frontend/src/modules/RequestModule.vue` — 模式切换、对话状态、装配/解析、流式编排、持久化。

---

## Task 1: 扩展后端数据模型

**Files:**
- Modify: `backend/models.py`
- Test: `tests/test_request_models.py`

- [ ] **Step 1: 写失败测试**

在 `tests/test_request_models.py` 末尾追加：

```python
def test_message_defaults():
    from backend.models import Message
    m = Message()
    assert m.role == "user"
    assert m.content == ""
    assert m.reasoning == ""


def test_conversation_defaults():
    from backend.models import Conversation
    c = Conversation(id="c1")
    assert c.name == "新对话"
    assert c.messages == []
    assert c.created_at == ""


def test_request_sample_chat_fields_default():
    from backend.models import RequestSample, RequestSpec
    s = RequestSample(id="s1", name="x", request=RequestSpec())
    assert s.mode == "request"
    assert s.conversations == []
    assert s.active_conversation_id is None


def test_request_sample_loads_legacy_without_chat_fields():
    # 旧 requests.json 没有新字段也能解析
    from backend.models import RequestSample
    s = RequestSample(**{"id": "s1", "name": "x", "request": {"method": "GET", "url": "u"}})
    assert s.conversations == []
    assert s.mode == "request"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_request_models.py -v`
Expected: FAIL（`ImportError: cannot import name 'Message'`）

- [ ] **Step 3: 实现模型**

在 `backend/models.py` 的 `RequestSample` 定义**之前**插入：

```python
class Message(BaseModel):
    role: Literal["system", "user", "assistant"] = "user"
    content: str = ""
    reasoning: str = ""


class Conversation(BaseModel):
    id: str
    name: str = "新对话"
    messages: list[Message] = []
    created_at: str = ""
    updated_at: str = ""
```

把现有 `RequestSample` 替换为：

```python
class RequestSample(BaseModel):
    id: str
    name: str
    request: RequestSpec
    mode: Literal["request", "chat"] = "request"
    conversations: list[Conversation] = []
    active_conversation_id: Optional[str] = None
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_request_models.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/models.py tests/test_request_models.py
git commit -m "feat: 数据模型新增 Message/Conversation 并扩展 RequestSample"
```

---

## Task 2: 上游 SSE 转换纯函数

**Files:**
- Create: `backend/services/chat_stream.py`
- Test: `tests/test_chat_stream.py`

- [ ] **Step 1: 写失败测试**

新建 `tests/test_chat_stream.py`：

```python
from backend.services.chat_stream import transform_sse_lines, format_sse


def collect(lines):
    return list(transform_sse_lines(lines))


def test_content_delta():
    events = collect(['data: {"choices":[{"delta":{"content":"你好"}}]}'])
    assert events == [("delta", {"content": "你好", "reasoning": ""})]


def test_reasoning_content_field():
    events = collect(['data: {"choices":[{"delta":{"reasoning_content":"想"}}]}'])
    assert events == [("delta", {"content": "", "reasoning": "想"})]


def test_reasoning_field_fallback():
    # 没有 reasoning_content 时回退到 reasoning
    events = collect(['data: {"choices":[{"delta":{"reasoning":"think"}}]}'])
    assert events == [("delta", {"content": "", "reasoning": "think"})]


def test_done_marker():
    events = collect(['data: {"choices":[{"delta":{"content":"a"}}]}', "data: [DONE]"])
    assert events == [("delta", {"content": "a", "reasoning": ""}), ("done", {})]


def test_skip_blank_and_bad_lines():
    events = collect(["", "  ", ": keep-alive", "data: not-json", 'data: {"choices":[]}'])
    assert events == []


def test_empty_delta_skipped():
    events = collect(['data: {"choices":[{"delta":{}}]}'])
    assert events == []


def test_format_sse_shape():
    out = format_sse("delta", {"content": "中"})
    assert out == 'event: delta\ndata: {"content": "中"}\n\n'
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_chat_stream.py -v`
Expected: FAIL（`ModuleNotFoundError: backend.services.chat_stream`）

- [ ] **Step 3: 实现纯函数**

新建 `backend/services/chat_stream.py`：

```python
import json
from typing import Iterable, Iterator, Tuple


def transform_sse_lines(lines: Iterable[str]) -> Iterator[Tuple[str, dict]]:
    """把上游 OpenAI 兼容 SSE 行流转换为 (event, data) 事件流。

    - data: [DONE]      -> ("done", {})
    - 含 content/reasoning 的 delta -> ("delta", {"content", "reasoning"})
    - 空行 / 非 data: 行 / 坏 JSON / 无 delta / 空 delta -> 跳过
    reasoning 字段兼容：reasoning_content（DeepSeek/vLLM）-> reasoning（OpenRouter）。
    """
    for raw in lines:
        line = (raw or "").strip()
        if not line.startswith("data:"):
            continue
        payload = line[len("data:"):].strip()
        if payload == "[DONE]":
            yield ("done", {})
            return
        try:
            obj = json.loads(payload)
        except (json.JSONDecodeError, ValueError):
            continue
        try:
            delta = obj["choices"][0]["delta"]
        except (KeyError, IndexError, TypeError):
            continue
        content = delta.get("content") or ""
        reasoning = delta.get("reasoning_content") or delta.get("reasoning") or ""
        if content or reasoning:
            yield ("delta", {"content": content, "reasoning": reasoning})


def format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_chat_stream.py -v`
Expected: PASS（7 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/services/chat_stream.py tests/test_chat_stream.py
git commit -m "feat: chat_stream 上游 SSE 转换纯函数 + 单测"
```

---

## Task 3: 流式运行器与路由

**Files:**
- Modify: `backend/services/chat_stream.py`
- Modify: `backend/routers/request.py`

- [ ] **Step 1: 在 chat_stream.py 增加运行器**

在 `backend/services/chat_stream.py` 顶部 import 改为：

```python
import json
from typing import Iterable, Iterator, Optional, Tuple

import httpx

from backend.models import RequestSpec

DEFAULT_TIMEOUT = 120.0
```

在文件末尾追加：

```python
def stream_chat(spec: RequestSpec, client: Optional[httpx.Client] = None) -> Iterator[str]:
    """连接上游 LLM，逐行转发为前端 SSE 字符串。"""
    headers = {h.key: h.value for h in spec.headers if h.enabled and h.key}
    content = spec.body.encode("utf-8") if spec.body else None
    owns = client is None
    try:
        if owns:
            client = httpx.Client(timeout=DEFAULT_TIMEOUT, follow_redirects=True, trust_env=False)
        with client.stream("POST", spec.url, headers=headers or None, content=content) as resp:
            if resp.status_code >= 400:
                body = resp.read().decode("utf-8", "replace")
                yield format_sse("error", {"message": f"上游 {resp.status_code}: {body[:500]}"})
                return
            for event, data in transform_sse_lines(resp.iter_lines()):
                yield format_sse(event, data)
    except Exception as e:  # noqa: BLE001 — 网络/超时统一回退为 error 事件
        yield format_sse("error", {"message": str(e) or e.__class__.__name__})
    finally:
        if owns and client is not None:
            client.close()
```

- [ ] **Step 2: 加路由**

在 `backend/routers/request.py` 顶部 import 增加：

```python
from fastapi.responses import StreamingResponse
from backend.services.chat_stream import stream_chat
```

在 `send` 路由之后追加：

```python
@router.post("/api/request/chat/stream")
def chat_stream(spec: RequestSpec):
    return StreamingResponse(stream_chat(spec), media_type="text/event-stream")
```

- [ ] **Step 3: 烟测路由已注册**

Run: `python -c "from backend.app import app; print([r.path for r in app.routes if 'chat' in r.path])"`
Expected: 输出包含 `/api/request/chat/stream`

- [ ] **Step 4: 回归后端测试**

Run: `python -m pytest tests/ -q`
Expected: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add backend/services/chat_stream.py backend/routers/request.py
git commit -m "feat: 流式对话端点 /api/request/chat/stream"
```

---

## Task 4: 前端流式 API 封装

**Files:**
- Modify: `frontend/src/api/index.js`

- [ ] **Step 1: 实现 chatStream**

在 `frontend/src/api/index.js` 末尾追加：

```javascript
// 解析单个 SSE 块（event: ... / data: ...）
function parseSSEChunk(chunk) {
  let event = 'message'
  let data = ''
  for (const line of chunk.split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim()
    else if (line.startsWith('data:')) data += line.slice(5).trim()
  }
  if (!data) return null
  try {
    return { event, data: JSON.parse(data) }
  } catch {
    return null
  }
}

// 流式对话：POST spec，逐块回调。onDelta({content,reasoning}) / onError(msg)。
// 返回 Promise，结束（done/流关闭/abort）后 resolve。
export async function chatStream(spec, { onDelta, onError, signal }) {
  let resp
  try {
    resp = await fetch('/api/request/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(spec),
      signal,
    })
  } catch (e) {
    if (e.name !== 'AbortError') onError(e.message)
    return
  }
  if (!resp.ok || !resp.body) {
    onError(`HTTP ${resp.status}`)
    return
  }
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buf = ''
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const chunks = buf.split('\n\n')
      buf = chunks.pop()
      for (const chunk of chunks) {
        const ev = parseSSEChunk(chunk)
        if (!ev) continue
        if (ev.event === 'delta') onDelta(ev.data)
        else if (ev.event === 'error') onError(ev.data.message || '上游错误')
      }
    }
  } catch (e) {
    if (e.name !== 'AbortError') onError(e.message)
  }
}
```

- [ ] **Step 2: 语法检查**

Run: `cd frontend && npx vite build --mode development 2>&1 | tail -5 || true`
Expected: 无 `api/index.js` 语法报错（若环境未装依赖，跳过，留待 Task 9 整体验证）

- [ ] **Step 3: 提交**

```bash
git add frontend/src/api/index.js
git commit -m "feat: 前端 chatStream fetch 流式封装"
```

---

## Task 5: MessageBubble 组件（气泡 + reasoning 折叠）

**Files:**
- Create: `frontend/src/components/request/MessageBubble.vue`

- [ ] **Step 1: 实现组件**

新建 `frontend/src/components/request/MessageBubble.vue`：

```vue
<template>
  <div class="msg" :class="message.role">
    <div v-if="message.reasoning" class="msg-reasoning">
      <button class="mr-toggle" @click="expanded = !expanded">
        <span class="mr-caret" :class="{ open: expanded }">▸</span>
        思考过程{{ streaming ? '（进行中…）' : '' }}
      </button>
      <pre v-show="expanded" class="mr-body">{{ message.reasoning }}</pre>
    </div>
    <div v-if="message.content" class="msg-content">{{ message.content }}</div>
    <div v-else-if="streaming && !message.reasoning" class="msg-content typing">…</div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  message: { type: Object, required: true },
  // 流式中：reasoning 默认展开；结束后自动折叠
  streaming: { type: Boolean, default: false },
})

const expanded = ref(props.streaming)
watch(
  () => props.streaming,
  (s) => { if (!s) expanded.value = false; else expanded.value = true }
)
</script>

<style scoped>
.msg { display: flex; flex-direction: column; gap: 6px; margin: 10px 0; max-width: 80%; }
.msg.user { align-self: flex-end; align-items: flex-end; }
.msg.assistant, .msg.system { align-self: flex-start; align-items: flex-start; }
.msg-content { padding: 10px 14px; border-radius: 14px; font-size: 14px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }
.msg.user .msg-content { background: var(--apple-primary, #007aff); color: #fff; }
.msg.assistant .msg-content { background: #f1f1f3; color: #1d1d1f; }
.msg.system .msg-content { background: #fff7e6; color: #8a6d3b; font-size: 13px; }
.msg-content.typing { color: #aaa; }
.msg-reasoning { width: 100%; }
.mr-toggle { border: none; background: none; color: #888; cursor: pointer; font-size: 12px; padding: 2px 0; display: inline-flex; align-items: center; gap: 4px; }
.mr-caret { display: inline-block; transition: transform 0.15s; }
.mr-caret.open { transform: rotate(90deg); }
.mr-body { margin: 4px 0 0; padding: 10px 12px; background: #fafafa; border-left: 2px solid #ddd; border-radius: 6px; font-size: 12px; color: #666; white-space: pre-wrap; word-break: break-word; max-height: 320px; overflow: auto; }
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/request/MessageBubble.vue
git commit -m "feat: MessageBubble 气泡 + reasoning 折叠"
```

---

## Task 6: ChatView 组件（渲染/输入/发送/停止/读流）

**Files:**
- Create: `frontend/src/components/request/ChatView.vue`

- [ ] **Step 1: 实现组件**

新建 `frontend/src/components/request/ChatView.vue`：

```vue
<template>
  <div class="chat-view">
    <div ref="scrollEl" class="cv-scroll">
      <div v-if="!messages.length" class="cv-empty">开始你的第一轮对话</div>
      <MessageBubble
        v-for="(m, i) in messages" :key="i"
        :message="m"
        :streaming="streaming && i === messages.length - 1 && m.role === 'assistant'"
      />
    </div>
    <div class="cv-input">
      <el-input
        v-model="draft" type="textarea" :rows="3" resize="none"
        placeholder="输入消息，Enter 发送，Shift+Enter 换行"
        @keydown.enter="onEnter"
      />
      <div class="cv-actions">
        <el-button v-if="streaming" type="danger" plain @click="emit('stop')">停止</el-button>
        <el-button v-else type="primary" :disabled="!draft.trim()" @click="onSend">发送</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import MessageBubble from './MessageBubble.vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  streaming: { type: Boolean, default: false },
})
const emit = defineEmits(['send', 'stop'])

const draft = ref('')
const scrollEl = ref(null)

function onSend() {
  const text = draft.value.trim()
  if (!text || props.streaming) return
  emit('send', text)
  draft.value = ''
}
function onEnter(e) {
  if (e.shiftKey) return
  e.preventDefault()
  onSend()
}

function scrollToBottom() {
  nextTick(() => {
    const el = scrollEl.value
    if (el) el.scrollTop = el.scrollHeight
  })
}
watch(() => props.messages, scrollToBottom, { deep: true })
</script>

<style scoped>
.chat-view { display: flex; flex-direction: column; flex: 1; min-height: 0; }
.cv-scroll { flex: 1; overflow: auto; display: flex; flex-direction: column; padding: 12px 16px; }
.cv-empty { margin: auto; color: #aaa; font-size: 14px; }
.cv-input { border-top: 1px solid var(--apple-hairline, rgba(0,0,0,0.08)); padding: 12px; display: flex; flex-direction: column; gap: 8px; }
.cv-actions { display: flex; justify-content: flex-end; }
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/request/ChatView.vue
git commit -m "feat: ChatView 对话主体（输入/发送/停止/滚动）"
```

---

## Task 7: ConversationList 组件（对话增删改查）

**Files:**
- Create: `frontend/src/components/request/ConversationList.vue`

- [ ] **Step 1: 实现组件**

新建 `frontend/src/components/request/ConversationList.vue`：

```vue
<template>
  <div class="conv-list">
    <div class="cl-header">
      <span>对话</span>
      <button class="cl-btn" @click="emit('new')">+新对话</button>
    </div>
    <div v-if="!conversations.length" class="cl-empty">暂无对话</div>
    <div
      v-for="c in conversations" :key="c.id"
      class="cl-item" :class="{ active: c.id === activeId }"
      @click="emit('select', c.id)"
    >
      <span class="cl-name">{{ c.name }}</span>
      <span class="cl-actions">
        <button class="cl-btn" @click.stop="rename(c)">rename</button>
        <button class="cl-btn del" @click.stop="confirmDelete(c)">del</button>
      </span>
    </div>
  </div>
</template>

<script setup>
import { ElMessageBox } from 'element-plus'

defineProps({
  conversations: { type: Array, default: () => [] },
  activeId: { type: String, default: '' },
})
const emit = defineEmits(['new', 'select', 'rename', 'delete'])

async function rename(c) {
  try {
    const { value } = await ElMessageBox.prompt('新名称', '重命名对话', { inputValue: c.name })
    if (value && value.trim()) emit('rename', { id: c.id, name: value.trim() })
  } catch (e) { /* 取消 */ }
}
async function confirmDelete(c) {
  try {
    await ElMessageBox.confirm(`确定删除对话「${c.name}」？`, '删除确认', { type: 'warning' })
    emit('delete', c.id)
  } catch (e) { /* 取消 */ }
}
</script>

<style scoped>
.conv-list { display: flex; flex-direction: column; }
.cl-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; font-weight: 600; font-size: 13px; color: #555; }
.cl-empty { padding: 10px 12px; color: #aaa; font-size: 13px; }
.cl-item { display: flex; align-items: center; gap: 8px; padding: 8px 12px; cursor: pointer; border-radius: 8px; margin: 0 6px; }
.cl-item:hover { background: rgba(0,122,255,0.06); }
.cl-item.active { background: rgba(0,122,255,0.12); }
.cl-name { flex: 1; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cl-actions { display: none; gap: 6px; }
.cl-item:hover .cl-actions { display: flex; }
.cl-btn { border: none; background: none; color: #888; cursor: pointer; font-size: 12px; padding: 0; }
.cl-btn:hover { color: var(--apple-primary, #007aff); }
.cl-btn.del:hover { color: #ff3b30; }
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/request/ConversationList.vue
git commit -m "feat: ConversationList 对话增删改查切换"
```

---

## Task 8: RequestBuilder 增加模式切换开关

**Files:**
- Modify: `frontend/src/components/request/RequestBuilder.vue`

- [ ] **Step 1: 增加 mode 开关**

在 `RequestBuilder.vue` 的 `props` 增加 `mode`，`emits` 增加 `update:mode`。

把 `props`/`emit` 定义改为：

```javascript
const props = defineProps({
  spec: { type: Object, required: true },
  loading: { type: Boolean, default: false },
  saveState: { type: String, default: '' },
  mode: { type: String, default: 'request' },
})
const emit = defineEmits(['update:spec', 'send', 'copy-curl', 'update:mode'])
```

在模板 `<div class="rb-tools">` 内、`复制为 curl` 按钮之前插入切换：

```html
      <el-radio-group
        :model-value="mode" size="small"
        @change="(v) => emit('update:mode', v)"
      >
        <el-radio-button value="request">请求</el-radio-button>
        <el-radio-button value="chat">对话</el-radio-button>
      </el-radio-group>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/request/RequestBuilder.vue
git commit -m "feat: RequestBuilder 顶部请求/对话模式切换"
```

---

## Task 9: RequestModule 集成（模式/对话/装配/流式/持久化）

**Files:**
- Modify: `frontend/src/modules/RequestModule.vue`

- [ ] **Step 1: 引入组件与 API**

把 import 段（第 35-41 行附近）补上：

```javascript
import ChatView from '../components/request/ChatView.vue'
import ConversationList from '../components/request/ConversationList.vue'
import { sendRequest, toCurl, getRequestSamples, saveRequestSamples, chatStream } from '../api'
```

- [ ] **Step 2: 增加辅助函数（装配/解析/当前对话）**

在 `<script setup>` 内 `isDraftMeaningful` 之后追加：

```javascript
function nowIso() {
  return new Date().toISOString()
}
// 从模板 body JSON 解析出 messages（切换 请求→对话 用）
function parseMessages(bodyStr) {
  try {
    const obj = JSON.parse(bodyStr || '{}')
    if (Array.isArray(obj.messages)) {
      return obj.messages.map((m) => ({
        role: m.role || 'user',
        content: typeof m.content === 'string' ? m.content : JSON.stringify(m.content),
        reasoning: '',
      }))
    }
  } catch (e) { /* 非 JSON */ }
  return []
}
// 模板 body + 对话 messages 装配为发送 body（切换 对话→请求、发送 用）
function assembleBody(bodyStr, messages) {
  let base = {}
  try { base = JSON.parse(bodyStr || '{}') } catch (e) { base = {} }
  return JSON.stringify({
    ...base,
    messages: messages.map((m) => ({ role: m.role, content: m.content })),
    stream: true,
  }, null, 2)
}
```

- [ ] **Step 3: 增加模式/对话状态**

在 `const saveState = ref('')` 之后追加：

```javascript
const mode = ref('request')
const streaming = ref(false)
let chatAbort = null

function activeSample() {
  return store.value.samples.find((s) => s.id === activeId.value)
}
function activeConversation() {
  const s = activeSample()
  if (!s) return null
  return (s.conversations || []).find((c) => c.id === s.active_conversation_id) || null
}
const currentMessages = ref([])
function syncMessagesRef() {
  const c = activeConversation()
  currentMessages.value = c ? c.messages : []
}
```

- [ ] **Step 4: 选中样例时同步 mode 与 messages**

在 `selectSample` 函数体开头（`if (s.id === activeId.value) return` 之后）和 `onMounted` 恢复选中处，统一通过新函数设置。把 `selectSample` 改为：

```javascript
function selectSample(s) {
  if (s.id === activeId.value) return
  activeId.value = s.id
  spec.value = { ...emptySpec(), ...snapshot(s.request) }
  mode.value = s.mode || 'request'
  if (!s.conversations) s.conversations = []
  if (mode.value === 'chat' && !s.active_conversation_id && s.conversations.length) {
    s.active_conversation_id = s.conversations[0].id
  }
  syncMessagesRef()
  persist().catch(() => {})
}
```

在 `onMounted` 内设置 `activeId`/`spec` 的两处之后，各加一行 `mode.value = target?.mode || 'request'`（迁移分支用 entry）并调用 `syncMessagesRef()`。具体：迁移分支 `spec.value = ...` 后加 `mode.value = 'request'; syncMessagesRef()`；恢复分支 `spec.value = ...` 后加 `mode.value = target.mode || 'request'; syncMessagesRef()`。

- [ ] **Step 5: 模式切换处理（双向同步）**

追加：

```javascript
function onModeChange(next) {
  const s = activeSample()
  if (!s) return
  if (next === 'chat') {
    if (!s.conversations) s.conversations = []
    if (!s.active_conversation_id || !activeConversation()) {
      const conv = { id: genId(), name: '新对话', messages: parseMessages(spec.value.body), created_at: nowIso(), updated_at: nowIso() }
      s.conversations.unshift(conv)
      s.active_conversation_id = conv.id
    }
    syncMessagesRef()
  } else {
    const c = activeConversation()
    if (c) {
      const next_body = assembleBody(spec.value.body, c.messages)
      spec.value = { ...spec.value, method: 'POST', body_type: 'json', body: next_body }
      s.request = snapshot(spec.value)
    }
  }
  mode.value = next
  s.mode = next
  persist().catch(() => {})
}
```

- [ ] **Step 6: 对话增删改查**

追加：

```javascript
function newConversation() {
  const s = activeSample()
  if (!s) return
  const conv = { id: genId(), name: '新对话', messages: [], created_at: nowIso(), updated_at: nowIso() }
  if (!s.conversations) s.conversations = []
  s.conversations.unshift(conv)
  s.active_conversation_id = conv.id
  syncMessagesRef()
  persist().catch(() => {})
}
function selectConversation(id) {
  const s = activeSample()
  if (!s) return
  s.active_conversation_id = id
  syncMessagesRef()
  persist().catch(() => {})
}
function renameConversation({ id, name }) {
  const s = activeSample()
  const c = s && s.conversations.find((x) => x.id === id)
  if (!c) return
  c.name = name
  persist().catch(() => {})
}
function deleteConversation(id) {
  const s = activeSample()
  if (!s) return
  s.conversations = s.conversations.filter((c) => c.id !== id)
  if (s.active_conversation_id === id) {
    s.active_conversation_id = s.conversations[0]?.id || null
  }
  syncMessagesRef()
  persist().catch(() => {})
}
```

- [ ] **Step 7: 发送一轮对话（流式）**

追加：

```javascript
async function sendChat(text) {
  const s = activeSample()
  const c = activeConversation()
  if (!s || !c || streaming.value) return
  c.messages.push({ role: 'user', content: text, reasoning: '' })
  const assistant = { role: 'assistant', content: '', reasoning: '' }
  c.messages.push(assistant)
  syncMessagesRef()
  streaming.value = true
  chatAbort = new AbortController()
  const chatSpec = { ...s.request, method: 'POST', body_type: 'json', body: assembleBody(s.request.body, c.messages.slice(0, -1)) }
  let errored = false
  await chatStream(chatSpec, {
    signal: chatAbort.signal,
    onDelta: (d) => {
      if (d.content) assistant.content += d.content
      if (d.reasoning) assistant.reasoning += d.reasoning
    },
    onError: (msg) => {
      errored = true
      ElMessage.error('对话失败：' + msg)
    },
  })
  streaming.value = false
  chatAbort = null
  if (errored && !assistant.content && !assistant.reasoning) {
    // 回滚未产出的 assistant 占位
    c.messages.pop()
  }
  c.updated_at = nowIso()
  syncMessagesRef()
  persist().catch(() => {})
}
function stopChat() {
  if (chatAbort) chatAbort.abort()
}
```

注意 `assembleBody(s.request.body, c.messages.slice(0, -1))`：发送时不包含刚追加的空 assistant 占位。

- [ ] **Step 8: 模板**

把 `<main class="rm-main">` 内的 `<template v-if="activeId">` 块替换为：

```html
      <template v-if="activeId">
        <RequestBuilder
          v-if="mode === 'request'"
          :spec="spec" :loading="sending" :save-state="saveState" :mode="mode"
          @update:spec="onSpecChange"
          @update:mode="onModeChange"
          @send="send"
          @copy-curl="copyCurl"
        />
        <ResponseView v-if="mode === 'request'" :response="response" :loading="sending" />
        <template v-else>
          <div class="rm-chat-bar">
            <el-radio-group :model-value="mode" size="small" @change="onModeChange">
              <el-radio-button value="request">请求</el-radio-button>
              <el-radio-button value="chat">对话</el-radio-button>
            </el-radio-group>
          </div>
          <div class="rm-chat-body">
            <aside class="rm-conv-side">
              <ConversationList
                :conversations="activeSample()?.conversations || []"
                :active-id="activeSample()?.active_conversation_id || ''"
                @new="newConversation" @select="selectConversation"
                @rename="renameConversation" @delete="deleteConversation"
              />
            </aside>
            <ChatView :messages="currentMessages" :streaming="streaming" @send="sendChat" @stop="stopChat" />
          </div>
        </template>
      </template>
```

- [ ] **Step 9: 样式**

在 `<style scoped>` 内追加：

```css
.rm-chat-bar { display: flex; justify-content: flex-end; }
.rm-chat-body { flex: 1; min-height: 0; display: flex; gap: 12px; }
.rm-conv-side { width: 200px; flex-shrink: 0; overflow: auto; border-right: 1px solid var(--apple-hairline, rgba(0,0,0,0.08)); }
```

并把 `.rm-main` 的 `overflow: auto` 改为 `overflow: hidden`（对话模式需内部各自滚动）：找到 `.rm-main { ... overflow: auto; ... }` 改 `overflow: hidden`。

- [ ] **Step 10: 手动验证（浏览器）**

启动后端：`python main.py --port 8002`；另起 `cd frontend && npm install && npm run dev`。
在浏览器打开 dev 地址，进入 postwoman：
1. 新建样例，URL 填一个 OpenAI 兼容 chat 接口，Headers 放 Authorization，Body 填 `{"model":"...","messages":[]}`。
2. 顶部切到「对话」→ 出现对话视图与对话列表。
3. 输入消息发送 → 回复逐字出现；若模型带 reasoning，思考过程流式展开、完成后折叠，可点开。
4. 「停止」可中断；已生成内容保留。
5. 「+新对话」「rename」「del」均生效；切换对话只换消息、配置不变。
6. 切回「请求」→ body 已拼接完整 messages，可复制为 curl。
7. 刷新页面 → 对话、选中、mode 都恢复（已持久化）。

Expected: 以上全部符合。

- [ ] **Step 11: 提交**

```bash
git add frontend/src/modules/RequestModule.vue
git commit -m "feat: RequestModule 集成对话模式（切换/对话管理/流式/持久化）"
```

---

## Self-Review 记录

- **Spec 覆盖**：模型(T1)、SSE 转换含 reasoning 双字段(T2)、流式端点(T3)、前端读流(T4)、reasoning 折叠(T5)、对话 UI(T6)、历史增删(T7)、模式开关(T8)、双向切换+装配+持久化(T9)。新对话空白起步 → T6 的 `newConversation` messages=[] ✓。
- **类型一致**：`Message{role,content,reasoning}` 前后端一致；`Conversation{id,name,messages,created_at,updated_at}` 一致；`assembleBody`/`parseMessages` 命名贯穿 T9。
- **无占位符**：各步均有完整代码与命令。
- **已知边界**：前端无 JS 测试框架，T4-T9 用浏览器手动验证（符合现状）；上游 SSE 解析以纯函数单测覆盖核心逻辑(T2)。
