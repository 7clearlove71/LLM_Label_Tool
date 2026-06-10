# 请求工具 Postman-lite 升级 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将请求工具收敛为 Postman-lite 模型：编辑区始终绑定当前样例并自动保存，新建 / 导入 curl / 克隆都直接生成左侧持久化样例。

**Architecture:** 后端 `RequestStore` 增 `active_id` 字段（仅一处改动 + 测试），其余持久化逻辑不变。前端 `RequestModule.vue` 重写编排（去 draft、自动写回当前样例、空状态、恢复选中），`SampleList`/`RequestBuilder` 配合改 UI。

**Tech Stack:** Python FastAPI + pydantic（后端，pytest）；Vue 3 + Element Plus（前端，无测试栈，UI 走手动验证）。

设计依据：`docs/superpowers/specs/2026-06-10-request-tool-postman-lite-design.md`

---

### Task 1: 后端 `RequestStore` 增加 `active_id`

**Files:**
- Modify: `backend/models.py:72-74`
- Test: `tests/test_request_models.py`、`tests/test_request_store.py`

- [ ] **Step 1: 写失败测试（模型默认值 + 往返 + 旧文件兼容）**

在 `tests/test_request_models.py` 末尾追加：

```python
def test_request_store_active_id_default():
    store = RequestStore()
    assert store.active_id is None
```

在 `tests/test_request_store.py` 末尾追加：

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_request_models.py::test_request_store_active_id_default tests/test_request_store.py::test_save_and_load_preserves_active_id tests/test_request_store.py::test_load_legacy_file_without_active_id -v`
Expected: FAIL（`AttributeError` / `TypeError`：`RequestStore` 无 `active_id`）

- [ ] **Step 3: 加字段**

`backend/models.py` 中 `RequestStore` 改为：

```python
class RequestStore(BaseModel):
    samples: list[RequestSample] = []
    draft: Optional[RequestSpec] = None
    active_id: Optional[str] = None
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_request_models.py tests/test_request_store.py -v`
Expected: PASS（含既有用例）

- [ ] **Step 5: 提交**

```bash
git add backend/models.py tests/test_request_models.py tests/test_request_store.py
git commit -m "feat: RequestStore 增加 active_id 字段(恢复选中)"
```

---

### Task 2: `SampleList.vue` —— 顶部新建/导入入口、克隆、删除确认

**Files:**
- Modify: `frontend/src/components/request/SampleList.vue`

- [ ] **Step 1: 替换组件内容**

将 `frontend/src/components/request/SampleList.vue` 整体替换为：

```vue
<template>
  <div class="sample-list">
    <div class="sl-header">
      <span>请求样例</span>
      <span class="sl-head-actions">
        <button class="sl-btn" @click="emit('new')">+新建</button>
        <button class="sl-btn" @click="emit('import-curl')">导入curl</button>
      </span>
    </div>
    <div v-if="!samples.length" class="sl-empty">暂无样例</div>
    <div
      v-for="s in samples"
      :key="s.id"
      class="sl-item"
      :class="{ active: s.id === activeId }"
      @click="emit('load', s)"
    >
      <span class="sl-method">{{ s.request.method }}</span>
      <span class="sl-name">{{ s.name }}</span>
      <span class="sl-actions">
        <button class="sl-btn" @click.stop="emit('clone', s)">克隆</button>
        <button class="sl-btn" @click.stop="rename(s)">改名</button>
        <button class="sl-btn del" @click.stop="confirmDelete(s)">删</button>
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
const emit = defineEmits(['new', 'import-curl', 'load', 'clone', 'delete', 'rename'])

async function rename(s) {
  try {
    const { value } = await ElMessageBox.prompt('新名称', '重命名', { inputValue: s.name })
    if (value && value.trim()) emit('rename', { id: s.id, name: value.trim() })
  } catch (e) { /* 取消 */ }
}

async function confirmDelete(s) {
  try {
    await ElMessageBox.confirm(`确定删除样例「${s.name}」？`, '删除确认', { type: 'warning' })
    emit('delete', s.id)
  } catch (e) { /* 取消 */ }
}
</script>

<style scoped>
.sample-list { display: flex; flex-direction: column; }
.sl-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 14px; font-weight: 600; font-size: 13px; color: #555; }
.sl-head-actions { display: flex; gap: 10px; }
.sl-empty { padding: 12px 14px; color: #aaa; font-size: 13px; }
.sl-item { display: flex; align-items: center; gap: 8px; padding: 10px 14px; cursor: pointer; border-radius: 8px; margin: 0 6px; }
.sl-item:hover { background: rgba(0,122,255,0.06); }
.sl-item.active { background: rgba(0,122,255,0.12); }
.sl-method { font-size: 11px; font-weight: 700; color: var(--apple-primary, #007aff); min-width: 38px; }
.sl-name { flex: 1; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sl-actions { display: none; gap: 6px; }
.sl-item:hover .sl-actions { display: flex; }
.sl-btn { border: none; background: none; color: #888; cursor: pointer; font-size: 12px; padding: 0; }
.sl-btn:hover { color: var(--apple-primary, #007aff); }
.sl-btn.del:hover { color: #ff3b30; }
</style>
```

- [ ] **Step 2: 提交（本任务与 Task 3、4 联调，可先单独提交结构改动）**

```bash
git add frontend/src/components/request/SampleList.vue
git commit -m "feat: SampleList 顶部新建/导入入口 + 克隆 + 删除确认"
```

---

### Task 3: `RequestBuilder.vue` —— 精简工具行 + 保存状态指示

**Files:**
- Modify: `frontend/src/components/request/RequestBuilder.vue`

- [ ] **Step 1: 替换组件内容**

将 `frontend/src/components/request/RequestBuilder.vue` 整体替换为：

```vue
<template>
  <div class="request-builder">
    <div class="rb-line">
      <el-select :model-value="spec.method" style="width: 110px" @change="(v) => update('method', v)">
        <el-option v-for="m in methods" :key="m" :label="m" :value="m" />
      </el-select>
      <el-input :model-value="spec.url" placeholder="请求 URL" class="rb-url" @input="(v) => update('url', v)" />
      <el-button type="primary" :loading="loading" @click="emit('send')">发送</el-button>
    </div>
    <div class="rb-tools">
      <button class="rb-tool" @click="emit('copy-curl')">复制为 curl</button>
      <span class="rb-save" v-if="saveState === 'saving'">保存中…</span>
      <span class="rb-save saved" v-else-if="saveState === 'saved'">已保存</span>
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
  saveState: { type: String, default: '' },
})
const emit = defineEmits(['update:spec', 'send', 'copy-curl'])

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
.rb-tools { display: flex; align-items: center; gap: 14px; }
.rb-tool { border: none; background: none; color: var(--apple-primary, #007aff); cursor: pointer; font-size: 13px; }
.rb-save { font-size: 12px; color: #999; }
.rb-save.saved { color: #34c759; }
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/request/RequestBuilder.vue
git commit -m "feat: RequestBuilder 精简工具行 + 保存状态指示"
```

---

### Task 4: `RequestModule.vue` —— 编排重写（自动保存 / 新建 / 克隆 / 导入入库 / 空状态 / 恢复选中 / draft 迁移）

**Files:**
- Modify: `frontend/src/modules/RequestModule.vue`

> 说明：实时编辑的自动保存失败时**不回滚正在输入的内容**（回滚会吞掉用户刚敲的字），仅提示错误并在下次编辑重试；结构性操作（新建 / 克隆 / 导入 / 删除）保持乐观写 + 失败回滚。

- [ ] **Step 1: 替换组件内容**

将 `frontend/src/modules/RequestModule.vue` 整体替换为：

```vue
<template>
  <div class="request-module">
    <aside class="rm-sidebar">
      <SampleList
        :samples="store.samples" :active-id="activeId"
        @new="newSample" @import-curl="showImport = true"
        @load="selectSample" @clone="cloneSample" @delete="deleteSample" @rename="renameSample"
      />
    </aside>
    <main class="rm-main">
      <template v-if="activeId">
        <RequestBuilder
          :spec="spec" :loading="sending" :save-state="saveState"
          @update:spec="onSpecChange"
          @send="send"
          @copy-curl="copyCurl"
        />
        <ResponseView :response="response" :loading="sending" />
      </template>
      <div v-else class="rm-empty">
        <p class="rm-empty-tip">还没有请求样例</p>
        <div class="rm-empty-actions">
          <el-button type="primary" @click="newSample">新建请求</el-button>
          <el-button @click="showImport = true">导入 curl</el-button>
        </div>
      </div>
    </main>

    <CurlImportDialog v-model="showImport" @imported="onCurlImported" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import SampleList from '../components/request/SampleList.vue'
import RequestBuilder from '../components/request/RequestBuilder.vue'
import ResponseView from '../components/request/ResponseView.vue'
import CurlImportDialog from '../components/request/CurlImportDialog.vue'
import { sendRequest, toCurl, getRequestSamples, saveRequestSamples } from '../api'

function emptySpec() {
  return { method: 'GET', url: '', params: [], headers: [], body_type: 'none', body: '', form_body: [] }
}
function snapshot(s) {
  return JSON.parse(JSON.stringify(s))
}
function genId() {
  return String(Date.now()) + '-' + Math.random().toString(36).slice(2, 6)
}
function nameFromUrl(url) {
  if (!url) return '导入的请求'
  try {
    const u = new URL(url)
    const name = (u.host + u.pathname).replace(/\/$/, '')
    return name || '导入的请求'
  } catch (e) {
    return '导入的请求'
  }
}
function isDraftMeaningful(d) {
  if (!d) return false
  return !!((d.url && d.url.trim()) || (d.method && d.method !== 'GET') ||
    (d.params && d.params.length) || (d.headers && d.headers.length) ||
    (d.body && d.body) || (d.form_body && d.form_body.length) ||
    (d.body_type && d.body_type !== 'none'))
}

const store = ref({ samples: [] })
const spec = ref(emptySpec())
const activeId = ref('')
const response = ref(null)
const sending = ref(false)
const showImport = ref(false)
const saveState = ref('')

let saveTimer = null

// 串行化所有 persist：避免并发 PUT 因网络重排互相覆盖。
let persistChain = Promise.resolve()
function persist() {
  const run = () => saveRequestSamples({ samples: store.value.samples, active_id: activeId.value })
  const result = persistChain.then(run, run)
  persistChain = result.catch(() => {})
  return result
}

onMounted(async () => {
  try {
    const { data } = await getRequestSamples()
    store.value = { samples: data.samples || [] }
    // 旧 draft 一次性迁移为样例
    if (isDraftMeaningful(data.draft)) {
      const entry = { id: genId(), name: '未命名请求', request: { ...emptySpec(), ...data.draft } }
      store.value.samples.push(entry)
      activeId.value = entry.id
      spec.value = { ...emptySpec(), ...snapshot(entry.request) }
      await persist() // 落库迁移结果（不再发送 draft）
      return
    }
    // 恢复上次选中，失败则选第一个
    const restore = data.active_id && store.value.samples.find((s) => s.id === data.active_id)
    const target = restore || store.value.samples[0]
    if (target) {
      activeId.value = target.id
      spec.value = { ...emptySpec(), ...snapshot(target.request) }
    }
  } catch (e) {
    ElMessage.error('加载样例失败：' + e.message)
  }
})

onUnmounted(() => {
  if (saveTimer) clearTimeout(saveTimer)
})

// 编辑当前样例：防抖自动保存，失败仅提示不回滚（避免吞掉输入）
function onSpecChange(next) {
  spec.value = next
  const target = store.value.samples.find((s) => s.id === activeId.value)
  if (!target) return
  target.request = snapshot(next)
  saveState.value = 'saving'
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    try {
      await persist()
      saveState.value = 'saved'
    } catch (e) {
      saveState.value = ''
      ElMessage.error('保存失败：' + (e.response?.data?.detail || e.message))
    }
  }, 500)
}

// 结构性新增：乐观写 + 失败回滚
async function addSampleAndSelect(entry) {
  const prevActive = activeId.value
  const prevSpec = spec.value
  store.value.samples.push(entry)
  activeId.value = entry.id
  spec.value = { ...emptySpec(), ...snapshot(entry.request) }
  saveState.value = 'saving'
  try {
    await persist()
    saveState.value = 'saved'
    return true
  } catch (e) {
    store.value.samples = store.value.samples.filter((s) => s.id !== entry.id)
    activeId.value = prevActive
    spec.value = prevSpec
    saveState.value = ''
    ElMessage.error('保存失败：' + (e.response?.data?.detail || e.message))
    return false
  }
}

function newSample() {
  return addSampleAndSelect({ id: genId(), name: '未命名请求', request: emptySpec() })
}

function cloneSample(s) {
  return addSampleAndSelect({ id: genId(), name: s.name + ' 副本', request: snapshot(s.request) })
}

async function onCurlImported(parsed) {
  const req = { ...emptySpec(), ...parsed }
  const ok = await addSampleAndSelect({ id: genId(), name: nameFromUrl(req.url), request: req })
  if (ok) ElMessage.success('已导入 curl 并新建样例')
}

function selectSample(s) {
  if (s.id === activeId.value) return
  activeId.value = s.id
  spec.value = { ...emptySpec(), ...snapshot(s.request) }
  saveState.value = 'saving'
  persist().then(() => { saveState.value = 'saved' }).catch(() => { saveState.value = '' })
}

async function renameSample({ id, name }) {
  const target = store.value.samples.find((s) => s.id === id)
  if (!target) return
  const prev = target.name
  target.name = name
  try {
    await persist()
  } catch (e) {
    target.name = prev
    ElMessage.error('重命名失败：' + (e.response?.data?.detail || e.message))
  }
}

async function deleteSample(id) {
  const prevSamples = store.value.samples
  const prevActive = activeId.value
  const prevSpec = spec.value
  store.value.samples = store.value.samples.filter((s) => s.id !== id)
  if (activeId.value === id) {
    const first = store.value.samples[0]
    if (first) {
      activeId.value = first.id
      spec.value = { ...emptySpec(), ...snapshot(first.request) }
    } else {
      activeId.value = ''
      spec.value = emptySpec()
    }
  }
  try {
    await persist()
  } catch (e) {
    store.value.samples = prevSamples
    activeId.value = prevActive
    spec.value = prevSpec
    ElMessage.error('删除样例失败：' + (e.response?.data?.detail || e.message))
  }
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
</script>

<style scoped>
.request-module { display: flex; flex: 1; min-height: 0; }
.rm-sidebar { width: 260px; flex-shrink: 0; overflow: auto; border-right: 1px solid var(--apple-hairline, rgba(0,0,0,0.08)); }
.rm-main { flex: 1; min-width: 0; overflow: auto; padding: 20px; display: flex; flex-direction: column; gap: 20px; }
.rm-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; color: #999; }
.rm-empty-tip { font-size: 14px; }
.rm-empty-actions { display: flex; gap: 12px; }
</style>
```

- [ ] **Step 2: 后端测试回归（确认未破坏后端）**

Run: `python -m pytest tests/ -v`
Expected: PASS（全绿）

- [ ] **Step 3: 手动验证前端（启动后端 + 前端 dev）**

启动：`python main.py --port 8002` 与 `cd frontend && npm run dev`，逐项确认：
1. 空状态：删空所有样例后主区显示「新建请求 / 导入 curl」按钮。
2. +新建：左侧出现「未命名请求」并选中，主区可编辑。
3. 导入 curl：粘贴一条 curl → 左侧出现以 URL 命名的新样例并选中，提示「已导入 curl 并新建样例」。
4. 编辑：改 URL/Header/Body → 工具行短暂显示「保存中…」后「已保存」；刷新页面内容与选中均恢复。
5. 克隆：hover 样例点「克隆」→ 出现「原名 副本」并选中。
6. 改名 / 删除：删除弹二次确认；删除当前选中后自动切到第一个或回空状态。
7. 旧数据迁移：若曾有 draft，首次加载后它变成「未命名请求」样例（无旧 draft 可跳过）。

- [ ] **Step 4: 提交**

```bash
git add frontend/src/modules/RequestModule.vue
git commit -m "feat: RequestModule 改为自动保存当前样例 + 新建/克隆/导入入库 + 空状态/恢复选中"
```

---

## 备注：前端无自动化测试

项目仅有 pytest 后端测试栈，无前端单测/E2E。Task 2-4 的前端行为以 Task 4 Step 3 的手动验证清单为准。后端字段改动（Task 1）以 pytest 覆盖。
