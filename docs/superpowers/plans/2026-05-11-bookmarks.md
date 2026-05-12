# 路径书签功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用户可以保存常用路径（最多10个），打开页面时通过点击标签快速扫描，无需手动输入。

**Architecture:** 后端新增 bookmarks router，读写项目根目录下的 `bookmarks.json` 文件。前端 PathInput 组件新增标签行，加载时获取书签列表，点击标签触发扫描，支持收藏/删除/设为默认。

**Tech Stack:** Python FastAPI, Pydantic, Vue 3, Element Plus (ElTag, ElButton, ElTooltip)

---

## 文件结构

| 操作 | 文件 | 职责 |
|------|------|------|
| 创建 | `backend/services/bookmark.py` | 书签读写逻辑 |
| 创建 | `backend/routers/bookmark.py` | 书签 API 路由 |
| 修改 | `backend/models.py` | 新增 BookmarksData 模型 |
| 修改 | `backend/app.py:17` | 注册 bookmark router |
| 修改 | `frontend/src/api/index.js` | 新增书签 API 调用 |
| 修改 | `frontend/src/components/PathInput.vue` | 标签行 UI + 收藏按钮 |
| 修改 | `frontend/src/App.vue` | 页面加载时自动扫描默认地址 |
| 创建 | `tests/test_bookmark.py` | 书签 API 测试 |

---

### Task 1: 后端书签数据模型

**Files:**
- Modify: `backend/models.py`

- [ ] **Step 1: 在 models.py 末尾添加 BookmarksData 模型**

```python
class BookmarksData(BaseModel):
    default: Optional[str] = None
    bookmarks: list[str] = []
```

- [ ] **Step 2: Commit**

```bash
git add backend/models.py
git commit -m "feat: 添加 BookmarksData 模型"
```

---

### Task 2: 后端书签服务

**Files:**
- Create: `backend/services/bookmark.py`
- Create: `tests/test_bookmark.py`

- [ ] **Step 1: 编写书签服务测试**

```python
# tests/test_bookmark.py
import json
import os
import pytest
from backend.services.bookmark import load_bookmarks, save_bookmarks
from backend.models import BookmarksData

@pytest.fixture
def bookmarks_file(tmp_path, monkeypatch):
    filepath = tmp_path / "bookmarks.json"
    monkeypatch.setattr("backend.services.bookmark.BOOKMARKS_PATH", str(filepath))
    return filepath

def test_load_bookmarks_file_not_exist(bookmarks_file):
    result = load_bookmarks()
    assert result.default is None
    assert result.bookmarks == []

def test_save_and_load_bookmarks(bookmarks_file):
    data = BookmarksData(default="/data/train", bookmarks=["/data/train", "/data/sft"])
    save_bookmarks(data)
    result = load_bookmarks()
    assert result.default == "/data/train"
    assert result.bookmarks == ["/data/train", "/data/sft"]

def test_save_bookmarks_limit(bookmarks_file):
    data = BookmarksData(bookmarks=[f"/path/{i}" for i in range(15)])
    save_bookmarks(data)
    result = load_bookmarks()
    assert len(result.bookmarks) == 10
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_bookmark.py -v`
Expected: FAIL — `backend.services.bookmark` 模块不存在

- [ ] **Step 3: 实现书签服务**

```python
# backend/services/bookmark.py
import json
import os
from backend.models import BookmarksData

BOOKMARKS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "bookmarks.json")
BOOKMARKS_PATH = os.path.normpath(BOOKMARKS_PATH)
MAX_BOOKMARKS = 10

def load_bookmarks() -> BookmarksData:
    if not os.path.isfile(BOOKMARKS_PATH):
        return BookmarksData()
    with open(BOOKMARKS_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return BookmarksData(**raw)

def save_bookmarks(data: BookmarksData) -> BookmarksData:
    data.bookmarks = data.bookmarks[:MAX_BOOKMARKS]
    with open(BOOKMARKS_PATH, "w", encoding="utf-8") as f:
        json.dump(data.model_dump(), f, ensure_ascii=False, indent=2)
    return data
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_bookmark.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add backend/services/bookmark.py tests/test_bookmark.py
git commit -m "feat: 实现书签服务层（读写 bookmarks.json）"
```

---

### Task 3: 后端书签 API 路由

**Files:**
- Create: `backend/routers/bookmark.py`
- Modify: `backend/app.py`
- Modify: `tests/test_bookmark.py`

- [ ] **Step 1: 在 tests/test_bookmark.py 末尾添加 API 测试**

```python
from httpx import AsyncClient, ASGITransport
from backend.app import create_app

@pytest.fixture
def app(bookmarks_file):
    return create_app()

@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.mark.anyio
async def test_get_bookmarks_empty(client):
    resp = await client.get("/api/bookmarks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["default"] is None
    assert data["bookmarks"] == []

@pytest.mark.anyio
async def test_put_bookmarks(client):
    payload = {"default": "/data/train", "bookmarks": ["/data/train", "/data/sft"]}
    resp = await client.put("/api/bookmarks", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["default"] == "/data/train"
    assert data["bookmarks"] == ["/data/train", "/data/sft"]

    resp2 = await client.get("/api/bookmarks")
    assert resp2.json()["default"] == "/data/train"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_bookmark.py::test_get_bookmarks_empty -v`
Expected: FAIL — 路由不存在，404

- [ ] **Step 3: 创建书签路由**

```python
# backend/routers/bookmark.py
from fastapi import APIRouter
from backend.models import BookmarksData
from backend.services.bookmark import load_bookmarks, save_bookmarks

router = APIRouter()

@router.get("/api/bookmarks")
def get_bookmarks() -> BookmarksData:
    return load_bookmarks()

@router.put("/api/bookmarks")
def put_bookmarks(data: BookmarksData) -> BookmarksData:
    return save_bookmarks(data)
```

- [ ] **Step 4: 在 app.py 中注册 router**

在 `backend/app.py` 中：
- import 行添加: `from backend.routers import scan, file, bookmark`
- include_router 后添加: `app.include_router(bookmark.router)`

- [ ] **Step 5: 运行测试确认通过**

Run: `python -m pytest tests/test_bookmark.py -v`
Expected: 全部通过

- [ ] **Step 6: Commit**

```bash
git add backend/routers/bookmark.py backend/app.py tests/test_bookmark.py
git commit -m "feat: 添加书签 API 路由 (GET/PUT /api/bookmarks)"
```

---

### Task 4: 前端 API 层添加书签接口

**Files:**
- Modify: `frontend/src/api/index.js`

- [ ] **Step 1: 在 api/index.js 末尾添加书签 API 函数**

```javascript
export function getBookmarks() {
  return api.get('/api/bookmarks')
}

export function saveBookmarks(data) {
  return api.put('/api/bookmarks', data)
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/index.js
git commit -m "feat: 前端 API 添加书签接口"
```

---

### Task 5: 前端 PathInput 组件改造

**Files:**
- Modify: `frontend/src/components/PathInput.vue`

- [ ] **Step 1: 重写 PathInput.vue**

完整替换 `PathInput.vue` 内容：

```vue
<template>
  <div class="path-input">
    <el-input
      v-model="path"
      placeholder="输入文件夹路径，如 /data/training"
      @keyup.enter="handleScan"
      size="default"
    >
      <template #append>
        <el-button @click="addBookmark" :disabled="!path.trim()" title="收藏当前路径">
          ★
        </el-button>
        <el-button @click="handleScan" :loading="loading">
          扫描
        </el-button>
      </template>
    </el-input>
    <div class="bookmark-tags" v-if="bookmarkData.bookmarks.length">
      <el-tag
        v-for="bm in bookmarkData.bookmarks"
        :key="bm"
        :type="bm === bookmarkData.default ? 'primary' : 'info'"
        closable
        @click="onTagClick(bm)"
        @close="removeBookmark(bm)"
        @contextmenu.prevent="setDefault(bm)"
        class="bookmark-tag"
      >
        <el-tooltip :content="bm" placement="top" :show-after="500">
          <span class="tag-label">{{ shortName(bm) }}</span>
        </el-tooltip>
      </el-tag>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getBookmarks, saveBookmarks } from '../api'

const emit = defineEmits(['scan'])
const path = ref('')
const loading = ref(false)
const bookmarkData = reactive({ default: null, bookmarks: [] })

onMounted(async () => {
  await fetchBookmarks()
  if (bookmarkData.default) {
    path.value = bookmarkData.default
    handleScan()
  }
})

async function fetchBookmarks() {
  try {
    const { data } = await getBookmarks()
    bookmarkData.default = data.default
    bookmarkData.bookmarks = data.bookmarks
  } catch {
    // 首次使用，无配置文件
  }
}

async function persistBookmarks() {
  await saveBookmarks({ default: bookmarkData.default, bookmarks: bookmarkData.bookmarks })
}

function handleScan() {
  if (!path.value.trim()) return
  loading.value = true
  try {
    emit('scan', path.value.trim())
  } finally {
    loading.value = false
  }
}

async function addBookmark() {
  const p = path.value.trim()
  if (!p) return
  if (bookmarkData.bookmarks.includes(p)) {
    ElMessage.info('该路径已收藏')
    return
  }
  if (bookmarkData.bookmarks.length >= 10) {
    ElMessage.warning('最多保存 10 个地址，请先删除一些')
    return
  }
  bookmarkData.bookmarks.push(p)
  if (!bookmarkData.default) {
    bookmarkData.default = p
  }
  await persistBookmarks()
  ElMessage.success('已收藏')
}

async function removeBookmark(bm) {
  bookmarkData.bookmarks = bookmarkData.bookmarks.filter(b => b !== bm)
  if (bookmarkData.default === bm) {
    bookmarkData.default = bookmarkData.bookmarks[0] || null
  }
  await persistBookmarks()
}

async function setDefault(bm) {
  bookmarkData.default = bm
  await persistBookmarks()
  ElMessage.success('已设为默认')
}

function onTagClick(bm) {
  path.value = bm
  handleScan()
}

function shortName(fullPath) {
  const parts = fullPath.replace(/\/+$/, '').split('/')
  return parts[parts.length - 1] || fullPath
}
</script>

<style scoped>
.path-input {
  padding: 16px;
  border-bottom: 1px solid #eee;
}

.bookmark-tags {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.bookmark-tag {
  cursor: pointer;
  max-width: 120px;
}

.tag-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
  max-width: 80px;
  vertical-align: middle;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/PathInput.vue
git commit -m "feat: PathInput 添加书签标签行、收藏按钮、右键设默认"
```

---

### Task 6: App.vue 接入默认地址自动扫描

**Files:**
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: 无需修改 App.vue**

自动扫描逻辑已在 PathInput 的 `onMounted` 中实现：加载书签后，如果有默认地址则自动 emit scan 事件。App.vue 已经监听了 `@scan="onScan"`，无需额外修改。

---

### Task 7: 端到端验证

- [ ] **Step 1: 运行后端测试**

Run: `python -m pytest tests/ -v`
Expected: 全部通过

- [ ] **Step 2: 构建前端并启动服务**

```bash
cd frontend && npm run build && cd ..
python main.py --port 8000
```

- [ ] **Step 3: 浏览器测试**

打开 http://localhost:8000，验证：
1. 输入路径 → 点击 ★ → 标签出现
2. 点击标签 → 自动扫描
3. 右键标签 → 设为默认（primary 高亮）
4. 刷新页面 → 自动扫描默认地址
5. 关闭标签 → 书签被删除
6. 检查项目根目录 `bookmarks.json` 文件内容正确
