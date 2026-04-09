# LLM 训练数据查看器 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 构建一个本地部署的 Web 工具，用于浏览、查看、搜索和编辑 JSON/JSONL 格式的 LLM 训练数据。

**架构：** FastAPI 后端提供 REST API，直接读写本地文件系统，无数据库。Vue 3 + Element Plus 前端 SPA，通过智能 schema 检测自适应渲染不同格式的训练数据。生产环境 FastAPI 直接 serve 前端静态文件，单端口部署。

**技术栈：** Python FastAPI, Vue 3, Vite, Element Plus, vue-json-pretty, uvicorn

---

## 文件结构

```
LLM_Label_Tool/
├── main.py                          # 入口：启动 FastAPI，serve 静态文件
├── backend/
│   ├── __init__.py
│   ├── app.py                       # FastAPI app 创建、路由挂载、CORS、静态文件
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── scan.py                  # /api/scan 接口：目录扫描
│   │   └── file.py                  # /api/file/* 接口：读取、编辑、删除、搜索、另存为
│   ├── services/
│   │   ├── __init__.py
│   │   ├── scanner.py               # 目录递归扫描，构建文件树
│   │   ├── reader.py                # 按行读取 JSON/JSONL，分页，行数缓存
│   │   ├── schema.py                # 智能 schema 检测，字段分类
│   │   ├── editor.py                # 行级编辑、删除、另存为
│   │   └── searcher.py              # 全文搜索、字段筛选
│   └── models.py                    # Pydantic 请求/响应模型
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # pytest fixtures（测试数据文件、FastAPI test client）
│   ├── test_scanner.py
│   ├── test_reader.py
│   ├── test_schema.py
│   ├── test_editor.py
│   ├── test_searcher.py
│   └── test_api.py                  # API 集成测试
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js                  # Vue app 入口
│       ├── App.vue                  # 根组件：双栏布局
│       ├── api/
│       │   └── index.js             # axios 封装，所有 API 调用
│       ├── components/
│       │   ├── PathInput.vue        # 顶栏：路径输入 + 扫描按钮
│       │   ├── FileTree.vue         # 左侧：el-tree 文件目录树
│       │   ├── DataView.vue         # 右侧主区域容器
│       │   ├── Toolbar.vue          # 搜索框 + 字段筛选 + 另存为
│       │   ├── DataTable.vue        # 数据表格，根据 schema 动态列
│       │   ├── PaginationBar.vue    # 分页 + 加载全部按钮
│       │   └── DetailDrawer.vue     # 右侧抽屉面板
│       └── renderers/
│           ├── ConversationView.vue # 对话气泡卡片渲染
│           ├── PreferenceView.vue   # 偏好对比（左右并排）渲染
│           ├── InstructionView.vue  # 指令三段式渲染
│           ├── JsonTreeView.vue     # JSON 树形视图（兜底）
│           └── EditorView.vue       # JSON 编辑器 + 保存/另存为
├── requirements.txt
└── .gitignore
```

---

### Task 1: 项目脚手架 & 开发环境搭建

**文件：**
- 创建: `requirements.txt`
- 创建: `backend/__init__.py`
- 创建: `backend/app.py`
- 修改: `main.py`
- 创建: `tests/__init__.py`
- 创建: `tests/conftest.py`
- 修改: `.gitignore`

- [ ] **Step 1: 创建 requirements.txt**

```
fastapi==0.115.0
uvicorn==0.30.0
pydantic==2.9.0
pytest==8.3.0
httpx==0.27.0
```

- [ ] **Step 2: 安装依赖**

运行: `cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool && pip install -r requirements.txt`
预期: 所有包安装成功

- [ ] **Step 3: 创建 backend/app.py — 最小 FastAPI 应用**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    app = FastAPI(title="LLM 训练数据查看器")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app
```

- [ ] **Step 4: 修改 main.py — 入口文件**

```python
import argparse
import uvicorn
from backend.app import create_app

app = create_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM 训练数据查看器")
    parser.add_argument("--port", type=int, default=8000, help="服务端口")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="监听地址")
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)
```

- [ ] **Step 5: 创建 tests/conftest.py**

```python
import json
import os
import tempfile
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app import create_app

@pytest.fixture
def app():
    return create_app()

@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.fixture
def sample_data_dir(tmp_path):
    """创建包含示例训练数据的临时目录"""
    # SFT 对话数据
    sft_dir = tmp_path / "sft_data"
    sft_dir.mkdir()
    sft_file = sft_dir / "chat.jsonl"
    lines = [
        json.dumps({"id": i, "messages": [
            {"role": "system", "content": "你是一个有用的助手"},
            {"role": "user", "content": f"问题{i}"},
            {"role": "assistant", "content": f"回答{i}"}
        ]}, ensure_ascii=False)
        for i in range(25)
    ]
    sft_file.write_text("\n".join(lines) + "\n")

    # RL 偏好数据
    rl_dir = tmp_path / "rl_data"
    rl_dir.mkdir()
    rl_file = rl_dir / "preference.json"
    lines_rl = [
        json.dumps({"id": i, "prompt": f"提示{i}", "chosen": f"好回答{i}", "rejected": f"差回答{i}"}, ensure_ascii=False)
        for i in range(15)
    ]
    rl_file.write_text("\n".join(lines_rl) + "\n")

    # 指令数据
    instruct_file = tmp_path / "instruct.json"
    lines_inst = [
        json.dumps({"instruction": f"指令{i}", "input": f"输入{i}", "output": f"输出{i}"}, ensure_ascii=False)
        for i in range(10)
    ]
    instruct_file.write_text("\n".join(lines_inst) + "\n")

    return tmp_path
```

- [ ] **Step 6: 更新 .gitignore**

追加以下内容：

```
__pycache__/
*.pyc
.pytest_cache/
node_modules/
dist/
frontend/dist/
.superpowers/
.env
```

- [ ] **Step 7: 写健康检查测试**

创建 `tests/test_api.py`:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app import create_app

@pytest.mark.asyncio
async def test_health():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
```

- [ ] **Step 8: 运行测试验证**

运行: `cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool && python -m pytest tests/test_api.py -v`
预期: 1 passed

- [ ] **Step 9: 提交**

```bash
git add requirements.txt backend/ tests/ main.py .gitignore
git commit -m "feat: 项目脚手架，FastAPI 最小应用 + 健康检查"
```

---

### Task 2: 目录扫描服务 & API

**文件：**
- 创建: `backend/models.py`
- 创建: `backend/services/__init__.py`
- 创建: `backend/services/scanner.py`
- 创建: `backend/routers/__init__.py`
- 创建: `backend/routers/scan.py`
- 修改: `backend/app.py`
- 创建: `tests/test_scanner.py`

- [ ] **Step 1: 写目录扫描的失败测试**

创建 `tests/test_scanner.py`:

```python
import json
from backend.services.scanner import scan_directory

def test_scan_finds_json_files(sample_data_dir):
    tree = scan_directory(str(sample_data_dir))
    # 根节点是目录本身
    assert tree["type"] == "directory"
    # 应该包含子目录和文件
    names = {child["name"] for child in tree["children"]}
    assert "sft_data" in names
    assert "rl_data" in names
    assert "instruct.json" in names

def test_scan_nested_structure(sample_data_dir):
    tree = scan_directory(str(sample_data_dir))
    sft = next(c for c in tree["children"] if c["name"] == "sft_data")
    assert sft["type"] == "directory"
    chat = next(c for c in sft["children"] if c["name"] == "chat.jsonl")
    assert chat["type"] == "file"
    assert chat["path"].endswith("chat.jsonl")
    assert chat["size"] > 0

def test_scan_ignores_non_json(sample_data_dir):
    # 创建一个非 json 文件
    (sample_data_dir / "readme.txt").write_text("hello")
    tree = scan_directory(str(sample_data_dir))
    names = {child["name"] for child in tree["children"]}
    assert "readme.txt" not in names

def test_scan_nonexistent_dir():
    tree = scan_directory("/nonexistent/path/12345")
    assert tree is None
```

- [ ] **Step 2: 运行测试确认失败**

运行: `python -m pytest tests/test_scanner.py -v`
预期: FAIL — ImportError

- [ ] **Step 3: 实现 scanner.py**

创建 `backend/services/__init__.py`（空文件）。

创建 `backend/services/scanner.py`:

```python
import os
from typing import Optional

def scan_directory(path: str) -> Optional[dict]:
    """递归扫描目录，返回仅包含 .json/.jsonl 文件的树形结构"""
    if not os.path.isdir(path):
        return None

    def build_tree(dir_path: str) -> dict:
        node = {
            "name": os.path.basename(dir_path),
            "path": dir_path,
            "type": "directory",
            "children": [],
        }
        try:
            entries = sorted(os.listdir(dir_path))
        except PermissionError:
            return node

        for entry in entries:
            full_path = os.path.join(dir_path, entry)
            if os.path.isdir(full_path):
                child = build_tree(full_path)
                # 只保留包含 json 文件的子目录
                if child["children"]:
                    node["children"].append(child)
            elif entry.endswith((".json", ".jsonl")):
                node["children"].append({
                    "name": entry,
                    "path": full_path,
                    "type": "file",
                    "size": os.path.getsize(full_path),
                })
        return node

    return build_tree(path)
```

- [ ] **Step 4: 运行测试验证通过**

运行: `python -m pytest tests/test_scanner.py -v`
预期: 4 passed

- [ ] **Step 5: 创建 Pydantic 模型**

创建 `backend/models.py`:

```python
from pydantic import BaseModel
from typing import Optional

class ScanRequest(BaseModel):
    path: str

class FileReadRequest(BaseModel):
    path: str
    offset: int = 0
    limit: int = 10

class FileReadAllRequest(BaseModel):
    path: str

class FileUpdateRequest(BaseModel):
    path: str
    row_index: int
    data: dict

class FileDeleteRequest(BaseModel):
    path: str
    row_index: int

class FileSaveAsRequest(BaseModel):
    source_path: str
    target_path: str

class FileSearchRequest(BaseModel):
    path: str
    keyword: str
    field: Optional[str] = None
```

- [ ] **Step 6: 创建扫描路由**

创建 `backend/routers/__init__.py`（空文件）。

创建 `backend/routers/scan.py`:

```python
from fastapi import APIRouter, HTTPException
from backend.models import ScanRequest
from backend.services.scanner import scan_directory

router = APIRouter()

@router.post("/api/scan")
def scan(req: ScanRequest):
    tree = scan_directory(req.path)
    if tree is None:
        raise HTTPException(status_code=400, detail="目录不存在")
    return tree
```

- [ ] **Step 7: 在 app.py 中挂载路由**

修改 `backend/app.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import scan

def create_app() -> FastAPI:
    app = FastAPI(title="LLM 训练数据查看器")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(scan.router)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app
```

- [ ] **Step 8: 写扫描 API 集成测试**

在 `tests/test_api.py` 中追加：

```python
@pytest.mark.asyncio
async def test_scan_api(sample_data_dir):
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/scan", json={"path": str(sample_data_dir)})
        assert resp.status_code == 200
        tree = resp.json()
        assert tree["type"] == "directory"
        names = {c["name"] for c in tree["children"]}
        assert "sft_data" in names

@pytest.mark.asyncio
async def test_scan_api_bad_path():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/scan", json={"path": "/nonexistent/12345"})
        assert resp.status_code == 400
```

- [ ] **Step 9: 运行全部测试**

运行: `python -m pytest tests/ -v`
预期: 全部通过

- [ ] **Step 10: 提交**

```bash
git add backend/ tests/
git commit -m "feat: 目录扫描服务和 /api/scan 接口"
```

---

### Task 3: 文件读取服务 & 智能 Schema 检测

**文件：**
- 创建: `backend/services/reader.py`
- 创建: `backend/services/schema.py`
- 创建: `tests/test_reader.py`
- 创建: `tests/test_schema.py`

- [ ] **Step 1: 写文件读取的失败测试**

创建 `tests/test_reader.py`:

```python
import json
from backend.services.reader import read_file, read_file_all, get_line_count

def test_read_file_default_10(sample_data_dir):
    path = str(sample_data_dir / "sft_data" / "chat.jsonl")
    result = read_file(path, offset=0, limit=10)
    assert len(result["rows"]) == 10
    assert result["total"] == 25
    assert result["rows"][0]["id"] == 0

def test_read_file_offset(sample_data_dir):
    path = str(sample_data_dir / "sft_data" / "chat.jsonl")
    result = read_file(path, offset=20, limit=10)
    assert len(result["rows"]) == 5  # 只剩 5 条
    assert result["rows"][0]["id"] == 20

def test_read_file_all(sample_data_dir):
    path = str(sample_data_dir / "rl_data" / "preference.json")
    result = read_file_all(path)
    assert len(result["rows"]) == 15
    assert result["total"] == 15

def test_get_line_count(sample_data_dir):
    path = str(sample_data_dir / "sft_data" / "chat.jsonl")
    assert get_line_count(path) == 25

def test_read_empty_file(tmp_path):
    empty = tmp_path / "empty.json"
    empty.write_text("")
    result = read_file(str(empty), 0, 10)
    assert result["rows"] == []
    assert result["total"] == 0
```

- [ ] **Step 2: 运行测试确认失败**

运行: `python -m pytest tests/test_reader.py -v`
预期: FAIL — ImportError

- [ ] **Step 3: 实现 reader.py**

创建 `backend/services/reader.py`:

```python
import json
from typing import Optional

# 行数缓存：{文件路径: 行数}
_line_count_cache: dict[str, int] = {}

def get_line_count(path: str) -> int:
    """获取文件的有效数据行数（跳过空行），带缓存"""
    if path in _line_count_cache:
        return _line_count_cache[path]
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    _line_count_cache[path] = count
    return count

def _read_lines(path: str, offset: int, limit: int) -> list[dict]:
    """按行读取文件，返回 offset 开始的 limit 条数据"""
    rows = []
    current = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            if current >= offset:
                rows.append(json.loads(stripped))
                if len(rows) >= limit:
                    break
            current += 1
    return rows

def read_file(path: str, offset: int = 0, limit: int = 10) -> dict:
    """读取文件的指定分页数据"""
    total = get_line_count(path)
    rows = _read_lines(path, offset, limit)
    return {"rows": rows, "total": total}

def read_file_all(path: str) -> dict:
    """读取文件的全部数据"""
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return {"rows": rows, "total": len(rows)}

def invalidate_cache(path: str):
    """清除指定文件的行数缓存"""
    _line_count_cache.pop(path, None)
```

- [ ] **Step 4: 运行测试验证通过**

运行: `python -m pytest tests/test_reader.py -v`
预期: 5 passed

- [ ] **Step 5: 写 schema 检测的失败测试**

创建 `tests/test_schema.py`:

```python
from backend.services.schema import detect_schema

def test_detect_conversation_schema():
    rows = [
        {"id": 0, "messages": [{"role": "user", "content": "你好"}, {"role": "assistant", "content": "嗨"}]},
        {"id": 1, "messages": [{"role": "user", "content": "再见"}]},
    ]
    schema = detect_schema(rows)
    fields = {f["name"]: f for f in schema["fields"]}
    assert fields["id"]["type"] == "number"
    assert fields["id"]["display"] == "column"
    assert fields["messages"]["pattern"] == "conversation"
    assert fields["messages"]["display"] == "detail"

def test_detect_preference_schema():
    rows = [
        {"id": 0, "prompt": "问题", "chosen": "好答案", "rejected": "差答案"},
    ]
    schema = detect_schema(rows)
    fields = {f["name"]: f for f in schema["fields"]}
    assert fields["chosen"]["pattern"] == "preference"
    assert fields["rejected"]["pattern"] == "preference"

def test_detect_instruction_schema():
    rows = [
        {"instruction": "翻译", "input": "hello", "output": "你好"},
    ]
    schema = detect_schema(rows)
    fields = {f["name"]: f for f in schema["fields"]}
    assert fields["instruction"]["pattern"] == "instruction"

def test_detect_long_string():
    rows = [{"text": "a" * 200}]
    schema = detect_schema(rows)
    fields = {f["name"]: f for f in schema["fields"]}
    assert fields["text"]["display"] == "detail"

def test_detect_generic_object():
    rows = [{"meta": {"key1": "val1", "key2": "val2"}}]
    schema = detect_schema(rows)
    fields = {f["name"]: f for f in schema["fields"]}
    assert fields["meta"]["type"] == "object"
    assert fields["meta"]["display"] == "detail"

def test_detect_empty_rows():
    schema = detect_schema([])
    assert schema["fields"] == []
```

- [ ] **Step 6: 运行测试确认失败**

运行: `python -m pytest tests/test_schema.py -v`
预期: FAIL — ImportError

- [ ] **Step 7: 实现 schema.py**

创建 `backend/services/schema.py`:

```python
from typing import Any

# 对话模式的特征字段
_CONVERSATION_KEYS = {"role", "content"}
# 偏好模式的特征字段
_PREFERENCE_KEYS = {"chosen", "rejected"}
# 指令模式的特征字段
_INSTRUCTION_KEYS = {"instruction", "input", "output"}

def _detect_field_type(values: list[Any]) -> dict:
    """分析某个字段在多条数据中的值，推断类型和展示方式"""
    non_none = [v for v in values if v is not None]
    if not non_none:
        return {"type": "unknown", "display": "column"}

    sample = non_none[0]

    # 数组类型
    if isinstance(sample, list):
        # 检查是否是对话模式：数组内的对象包含 role + content
        if (len(non_none) > 0 and
            all(isinstance(v, list) for v in non_none) and
            any(len(v) > 0 for v in non_none)):
            flat_items = [item for v in non_none for item in v if isinstance(item, dict)]
            if flat_items and _CONVERSATION_KEYS.issubset(flat_items[0].keys()):
                children = [{"name": k, "type": "string"} for k in flat_items[0].keys()]
                return {"type": "array<object>", "display": "detail", "pattern": "conversation", "children": children}
        return {"type": "array", "display": "detail"}

    # 对象类型
    if isinstance(sample, dict):
        return {"type": "object", "display": "detail"}

    # 布尔
    if isinstance(sample, bool):
        return {"type": "boolean", "display": "column"}

    # 数字
    if isinstance(sample, (int, float)):
        return {"type": "number", "display": "column"}

    # 字符串
    if isinstance(sample, str):
        max_len = max(len(str(v)) for v in non_none)
        if max_len >= 100:
            return {"type": "string", "display": "detail"}
        return {"type": "string", "display": "column"}

    return {"type": "unknown", "display": "column"}

def detect_schema(rows: list[dict]) -> dict:
    """分析数据行，生成字段 schema"""
    if not rows:
        return {"fields": []}

    # 收集所有字段名（按首次出现排序）
    field_names: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                field_names.append(key)
                seen.add(key)

    # 检测全局数据模式（偏好、指令）
    all_keys = set(field_names)
    has_preference = _PREFERENCE_KEYS.issubset(all_keys)
    has_instruction = _INSTRUCTION_KEYS.issubset(all_keys)

    fields = []
    for name in field_names:
        values = [row.get(name) for row in rows]
        field_info = _detect_field_type(values)
        field_info["name"] = name

        # 标记偏好模式字段
        if has_preference and name in _PREFERENCE_KEYS:
            field_info["pattern"] = "preference"
            field_info["display"] = "detail"

        # 标记指令模式字段
        if has_instruction and name in _INSTRUCTION_KEYS:
            field_info["pattern"] = "instruction"
            field_info["display"] = "detail"

        fields.append(field_info)

    return {"fields": fields}
```

- [ ] **Step 8: 运行测试验证通过**

运行: `python -m pytest tests/test_schema.py -v`
预期: 6 passed

- [ ] **Step 9: 提交**

```bash
git add backend/services/ tests/test_reader.py tests/test_schema.py
git commit -m "feat: 文件按行读取服务和智能 schema 检测"
```

---

### Task 4: 编辑、删除、搜索服务

**文件：**
- 创建: `backend/services/editor.py`
- 创建: `backend/services/searcher.py`
- 创建: `tests/test_editor.py`
- 创建: `tests/test_searcher.py`

- [ ] **Step 1: 写编辑服务的失败测试**

创建 `tests/test_editor.py`:

```python
import json
from backend.services.editor import update_row, delete_row, save_as

def test_update_row(sample_data_dir):
    path = str(sample_data_dir / "instruct.json")
    new_data = {"instruction": "新指令", "input": "新输入", "output": "新输出"}
    update_row(path, 0, new_data)
    with open(path, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()
    assert json.loads(first_line) == new_data

def test_update_row_middle(sample_data_dir):
    path = str(sample_data_dir / "instruct.json")
    new_data = {"instruction": "中间修改", "input": "", "output": ""}
    update_row(path, 5, new_data)
    with open(path, "r", encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]
    assert json.loads(lines[5].strip()) == new_data
    assert len(lines) == 10  # 总行数不变

def test_delete_row(sample_data_dir):
    path = str(sample_data_dir / "instruct.json")
    delete_row(path, 0)
    with open(path, "r", encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]
    assert len(lines) == 9
    assert json.loads(lines[0].strip())["instruction"] == "指令1"

def test_save_as(sample_data_dir):
    source = str(sample_data_dir / "instruct.json")
    target = str(sample_data_dir / "instruct_copy.json")
    save_as(source, target)
    with open(target, "r", encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]
    assert len(lines) == 10
```

- [ ] **Step 2: 运行测试确认失败**

运行: `python -m pytest tests/test_editor.py -v`
预期: FAIL — ImportError

- [ ] **Step 3: 实现 editor.py**

创建 `backend/services/editor.py`:

```python
import json
import shutil
from backend.services.reader import invalidate_cache

def _read_all_lines(path: str) -> list[str]:
    """读取文件所有非空行"""
    with open(path, "r", encoding="utf-8") as f:
        return [line for line in f if line.strip()]

def _write_all_lines(path: str, lines: list[str]):
    """将所有行写回文件"""
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            if not line.endswith("\n"):
                line += "\n"
            f.write(line)
    invalidate_cache(path)

def update_row(path: str, row_index: int, data: dict):
    """更新文件中指定行的数据"""
    lines = _read_all_lines(path)
    if row_index < 0 or row_index >= len(lines):
        raise IndexError(f"行索引 {row_index} 超出范围（共 {len(lines)} 行）")
    lines[row_index] = json.dumps(data, ensure_ascii=False) + "\n"
    _write_all_lines(path, lines)

def delete_row(path: str, row_index: int):
    """删除文件中指定行"""
    lines = _read_all_lines(path)
    if row_index < 0 or row_index >= len(lines):
        raise IndexError(f"行索引 {row_index} 超出范围（共 {len(lines)} 行）")
    lines.pop(row_index)
    _write_all_lines(path, lines)

def save_as(source_path: str, target_path: str):
    """将源文件另存为目标路径"""
    shutil.copy2(source_path, target_path)
```

- [ ] **Step 4: 运行测试验证通过**

运行: `python -m pytest tests/test_editor.py -v`
预期: 4 passed

- [ ] **Step 5: 写搜索服务的失败测试**

创建 `tests/test_searcher.py`:

```python
import json
from backend.services.searcher import search_file

def test_search_keyword(sample_data_dir):
    path = str(sample_data_dir / "sft_data" / "chat.jsonl")
    results = search_file(path, keyword="问题3")
    assert len(results) == 1
    assert results[0]["row_index"] == 3

def test_search_keyword_multiple_matches(sample_data_dir):
    path = str(sample_data_dir / "sft_data" / "chat.jsonl")
    results = search_file(path, keyword="问题1")
    # 匹配 问题1, 问题10, 问题11, ..., 问题19
    assert len(results) == 11

def test_search_with_field(sample_data_dir):
    path = str(sample_data_dir / "rl_data" / "preference.json")
    results = search_file(path, keyword="好回答5", field="chosen")
    assert len(results) == 1
    assert results[0]["data"]["chosen"] == "好回答5"

def test_search_no_match(sample_data_dir):
    path = str(sample_data_dir / "instruct.json")
    results = search_file(path, keyword="不存在的内容xyz")
    assert results == []
```

- [ ] **Step 6: 运行测试确认失败**

运行: `python -m pytest tests/test_searcher.py -v`
预期: FAIL — ImportError

- [ ] **Step 7: 实现 searcher.py**

创建 `backend/services/searcher.py`:

```python
import json
from typing import Optional

def search_file(path: str, keyword: str, field: Optional[str] = None) -> list[dict]:
    """搜索文件中匹配关键词的行"""
    results = []
    row_index = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            data = json.loads(stripped)
            matched = False
            if field:
                # 字段级搜索
                value = data.get(field)
                if value is not None and keyword in json.dumps(value, ensure_ascii=False):
                    matched = True
            else:
                # 全文搜索：在整行 JSON 中搜索
                if keyword in stripped:
                    matched = True
            if matched:
                results.append({"row_index": row_index, "data": data})
            row_index += 1
    return results
```

- [ ] **Step 8: 运行测试验证通过**

运行: `python -m pytest tests/test_searcher.py -v`
预期: 4 passed

- [ ] **Step 9: 提交**

```bash
git add backend/services/editor.py backend/services/searcher.py tests/test_editor.py tests/test_searcher.py
git commit -m "feat: 编辑、删除、搜索服务"
```

---

### Task 5: 文件操作 API 路由

**文件：**
- 创建: `backend/routers/file.py`
- 修改: `backend/app.py`
- 修改: `tests/test_api.py`

- [ ] **Step 1: 创建文件操作路由**

创建 `backend/routers/file.py`:

```python
from fastapi import APIRouter, HTTPException
from backend.models import (
    FileReadRequest, FileReadAllRequest, FileUpdateRequest,
    FileDeleteRequest, FileSaveAsRequest, FileSearchRequest,
)
from backend.services.reader import read_file, read_file_all
from backend.services.schema import detect_schema
from backend.services.editor import update_row, delete_row, save_as
from backend.services.searcher import search_file

router = APIRouter(prefix="/api/file")

@router.post("/read")
def file_read(req: FileReadRequest):
    try:
        result = read_file(req.path, req.offset, req.limit)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    schema = detect_schema(result["rows"])
    return {**result, "schema": schema}

@router.post("/read-all")
def file_read_all(req: FileReadAllRequest):
    try:
        result = read_file_all(req.path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在")
    schema = detect_schema(result["rows"][:10])
    return {**result, "schema": schema}

@router.post("/update")
def file_update(req: FileUpdateRequest):
    try:
        update_row(req.path, req.row_index, req.data)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在")
    except IndexError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok"}

@router.post("/delete")
def file_delete(req: FileDeleteRequest):
    try:
        delete_row(req.path, req.row_index)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在")
    except IndexError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok"}

@router.post("/save-as")
def file_save_as(req: FileSaveAsRequest):
    try:
        save_as(req.source_path, req.target_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="源文件不存在")
    return {"status": "ok"}

@router.post("/search")
def file_search(req: FileSearchRequest):
    try:
        results = search_file(req.path, req.keyword, req.field)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在")
    return {"results": results, "count": len(results)}
```

- [ ] **Step 2: 在 app.py 中挂载文件路由**

修改 `backend/app.py`，在 `app.include_router(scan.router)` 后追加：

```python
from backend.routers import scan, file

app.include_router(scan.router)
app.include_router(file.router)
```

- [ ] **Step 3: 写 API 集成测试**

在 `tests/test_api.py` 中追加：

```python
@pytest.mark.asyncio
async def test_file_read_api(sample_data_dir):
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        path = str(sample_data_dir / "sft_data" / "chat.jsonl")
        resp = await client.post("/api/file/read", json={"path": path, "offset": 0, "limit": 10})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["rows"]) == 10
        assert body["total"] == 25
        assert "schema" in body
        assert len(body["schema"]["fields"]) > 0

@pytest.mark.asyncio
async def test_file_read_all_api(sample_data_dir):
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        path = str(sample_data_dir / "instruct.json")
        resp = await client.post("/api/file/read-all", json={"path": path})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["rows"]) == 10
        assert body["total"] == 10

@pytest.mark.asyncio
async def test_file_update_api(sample_data_dir):
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        path = str(sample_data_dir / "instruct.json")
        new_data = {"instruction": "更新", "input": "x", "output": "y"}
        resp = await client.post("/api/file/update", json={
            "path": path, "row_index": 0, "data": new_data
        })
        assert resp.status_code == 200
        # 验证更新生效
        resp2 = await client.post("/api/file/read", json={"path": path, "offset": 0, "limit": 1})
        assert resp2.json()["rows"][0]["instruction"] == "更新"

@pytest.mark.asyncio
async def test_file_search_api(sample_data_dir):
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        path = str(sample_data_dir / "rl_data" / "preference.json")
        resp = await client.post("/api/file/search", json={
            "path": path, "keyword": "好回答5"
        })
        assert resp.status_code == 200
        assert resp.json()["count"] == 1
```

- [ ] **Step 4: 运行全部测试**

运行: `python -m pytest tests/ -v`
预期: 全部通过

- [ ] **Step 5: 提交**

```bash
git add backend/routers/file.py backend/app.py tests/test_api.py
git commit -m "feat: 文件读取、编辑、搜索 API 路由"
```

---

### Task 6: Vue 3 前端脚手架

**文件：**
- 创建: `frontend/package.json`
- 创建: `frontend/vite.config.js`
- 创建: `frontend/index.html`
- 创建: `frontend/src/main.js`
- 创建: `frontend/src/App.vue`
- 创建: `frontend/src/api/index.js`

- [ ] **Step 1: 初始化前端项目**

```bash
cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool
npm create vite@latest frontend -- --template vue
cd frontend
npm install
npm install element-plus vue-json-pretty axios
```

- [ ] **Step 2: 配置 vite.config.js**

覆盖 `frontend/vite.config.js`:

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../backend/static',
    emptyOutDir: true,
  },
})
```

- [ ] **Step 3: 创建 API 封装层**

创建 `frontend/src/api/index.js`:

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: '',
  timeout: 30000,
})

export function scanDirectory(path) {
  return api.post('/api/scan', { path })
}

export function readFile(path, offset = 0, limit = 10) {
  return api.post('/api/file/read', { path, offset, limit })
}

export function readFileAll(path) {
  return api.post('/api/file/read-all', { path })
}

export function updateRow(path, rowIndex, data) {
  return api.post('/api/file/update', { path, row_index: rowIndex, data })
}

export function deleteRow(path, rowIndex) {
  return api.post('/api/file/delete', { path, row_index: rowIndex })
}

export function saveAs(sourcePath, targetPath) {
  return api.post('/api/file/save-as', { source_path: sourcePath, target_path: targetPath })
}

export function searchFile(path, keyword, field = null) {
  return api.post('/api/file/search', { path, keyword, field })
}
```

- [ ] **Step 4: 创建 main.js 入口**

覆盖 `frontend/src/main.js`:

```javascript
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'

const app = createApp(App)
app.use(ElementPlus)
app.mount('#app')
```

- [ ] **Step 5: 创建 App.vue 骨架布局**

覆盖 `frontend/src/App.vue`:

```vue
<template>
  <div class="app">
    <header class="app-header">
      <h1 class="app-title">LLM 训练数据查看器</h1>
    </header>
    <div class="app-body">
      <aside class="sidebar">
        <PathInput @scan="onScan" />
        <FileTree :tree="fileTree" @select="onFileSelect" />
      </aside>
      <main class="main-content">
        <DataView
          :file-path="selectedFile"
          :key="selectedFile"
        />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import PathInput from './components/PathInput.vue'
import FileTree from './components/FileTree.vue'
import DataView from './components/DataView.vue'
import { scanDirectory } from './api'

const fileTree = ref(null)
const selectedFile = ref('')

async function onScan(path) {
  const { data } = await scanDirectory(path)
  fileTree.value = data
}

function onFileSelect(filePath) {
  selectedFile.value = filePath
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #ffffff;
  color: #333333;
}

.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  height: 56px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #eee;
  background: #ffffff;
}

.app-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.app-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar {
  width: 280px;
  border-right: 1px solid #eee;
  background: #f7f8fa;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.main-content {
  flex: 1;
  overflow: hidden;
  background: #ffffff;
}
</style>
```

- [ ] **Step 6: 验证前端启动**

```bash
cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool/frontend && npm run dev
```

预期: Vite 启动，浏览器打开 http://localhost:5173 可看到页面骨架（标题和空白布局）。暂时会有组件导入错误，下一步创建。按 Ctrl+C 停止。

- [ ] **Step 7: 提交**

```bash
git add frontend/
git commit -m "feat: Vue 3 前端脚手架，App 骨架布局 + API 封装"
```

---

### Task 7: PathInput 和 FileTree 组件

**文件：**
- 创建: `frontend/src/components/PathInput.vue`
- 创建: `frontend/src/components/FileTree.vue`

- [ ] **Step 1: 创建 PathInput 组件**

创建 `frontend/src/components/PathInput.vue`:

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
        <el-button @click="handleScan" :loading="loading">
          扫描
        </el-button>
      </template>
    </el-input>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['scan'])
const path = ref('')
const loading = ref(false)

async function handleScan() {
  if (!path.value.trim()) return
  loading.value = true
  try {
    emit('scan', path.value.trim())
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.path-input {
  padding: 16px;
  border-bottom: 1px solid #eee;
}
</style>
```

- [ ] **Step 2: 创建 FileTree 组件**

创建 `frontend/src/components/FileTree.vue`:

```vue
<template>
  <div class="file-tree">
    <el-tree
      v-if="treeData.length"
      :data="treeData"
      :props="treeProps"
      node-key="path"
      highlight-current
      :expand-on-click-node="false"
      @node-click="handleNodeClick"
    >
      <template #default="{ node, data }">
        <span class="tree-node">
          <span class="node-icon">{{ data.type === 'directory' ? '📁' : '📄' }}</span>
          <span class="node-label">{{ data.name }}</span>
          <span v-if="data.type === 'file'" class="node-size">
            {{ formatSize(data.size) }}
          </span>
        </span>
      </template>
    </el-tree>
    <div v-else class="empty-tip">请输入路径并扫描</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  tree: { type: Object, default: null },
})

const emit = defineEmits(['select'])

const treeProps = {
  children: 'children',
  label: 'name',
  isLeaf: (data) => data.type === 'file',
}

const treeData = computed(() => {
  if (!props.tree) return []
  return props.tree.children || []
})

function handleNodeClick(data) {
  if (data.type === 'file') {
    emit('select', data.path)
  }
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.file-tree {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  width: 100%;
}

.node-icon {
  font-size: 14px;
}

.node-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-size {
  color: #999;
  font-size: 11px;
  flex-shrink: 0;
}

.empty-tip {
  padding: 24px;
  text-align: center;
  color: #999;
  font-size: 13px;
}
</style>
```

- [ ] **Step 3: 验证前端运行**

同时启动后端和前端：

终端 1:
```bash
cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool && python main.py --port 8000
```

终端 2:
```bash
cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool/frontend && npm run dev
```

打开 http://localhost:5173，输入一个包含 json 文件的路径，点击扫描，应该能看到左侧文件树。

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/PathInput.vue frontend/src/components/FileTree.vue
git commit -m "feat: PathInput 路径输入和 FileTree 文件树组件"
```

---

### Task 8: DataView、DataTable 和 Pagination 组件

**文件：**
- 创建: `frontend/src/components/DataView.vue`
- 创建: `frontend/src/components/DataTable.vue`
- 创建: `frontend/src/components/Toolbar.vue`
- 创建: `frontend/src/components/PaginationBar.vue`

- [ ] **Step 1: 创建 Toolbar 组件**

创建 `frontend/src/components/Toolbar.vue`:

```vue
<template>
  <div class="toolbar">
    <el-input
      v-model="keyword"
      placeholder="搜索内容..."
      clearable
      size="default"
      class="search-input"
      @keyup.enter="handleSearch"
    >
      <template #prefix>
        <el-icon><Search /></el-icon>
      </template>
    </el-input>
    <el-select
      v-model="selectedField"
      placeholder="全部字段"
      clearable
      size="default"
      class="field-select"
    >
      <el-option
        v-for="field in fields"
        :key="field.name"
        :label="field.name"
        :value="field.name"
      />
    </el-select>
    <el-button @click="handleSearch" size="default" type="primary" plain>
      搜索
    </el-button>
    <el-button @click="$emit('save-as')" size="default" plain>
      另存为
    </el-button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps({
  fields: { type: Array, default: () => [] },
})

const emit = defineEmits(['search', 'save-as'])
const keyword = ref('')
const selectedField = ref('')

function handleSearch() {
  emit('search', { keyword: keyword.value, field: selectedField.value || null })
}
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  border-bottom: 1px solid #eee;
}

.search-input {
  width: 280px;
}

.field-select {
  width: 150px;
}
</style>
```

- [ ] **Step 2: 创建 DataTable 组件**

创建 `frontend/src/components/DataTable.vue`:

```vue
<template>
  <div class="data-table-wrapper">
    <el-table
      :data="rows"
      stripe
      highlight-current-row
      @row-click="handleRowClick"
      class="data-table"
      :header-cell-style="{ background: '#f7f8fa', color: '#333', fontWeight: 600 }"
    >
      <el-table-column type="index" label="#" width="60" :index="indexMethod" />
      <el-table-column
        v-for="field in columnFields"
        :key="field.name"
        :prop="field.name"
        :label="field.name"
        :min-width="getColumnWidth(field)"
        show-overflow-tooltip
      >
        <template #default="{ row }">
          <span v-if="isSimpleValue(row[field.name])">
            {{ row[field.name] }}
          </span>
          <span v-else class="complex-value">
            {{ summarize(row[field.name]) }}
          </span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  schema: { type: Object, default: () => ({ fields: [] }) },
  offset: { type: Number, default: 0 },
})

const emit = defineEmits(['row-click'])

const columnFields = computed(() => {
  return props.schema.fields || []
})

function indexMethod(index) {
  return props.offset + index + 1
}

function handleRowClick(row, column, event) {
  const rowIndex = props.rows.indexOf(row)
  emit('row-click', { row, index: props.offset + rowIndex })
}

function isSimpleValue(val) {
  return val === null || val === undefined || typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean'
}

function summarize(val) {
  if (Array.isArray(val)) return `[${val.length} items]`
  if (typeof val === 'object' && val !== null) return `{${Object.keys(val).length} keys}`
  return String(val)
}

function getColumnWidth(field) {
  if (field.type === 'number' || field.type === 'boolean') return '100'
  if (field.display === 'detail') return '150'
  return '180'
}
</script>

<style scoped>
.data-table-wrapper {
  flex: 1;
  overflow: auto;
  padding: 0 24px;
}

.data-table {
  width: 100%;
}

.complex-value {
  color: #999;
  font-style: italic;
  cursor: pointer;
}

.complex-value:hover {
  color: #409eff;
}
</style>
```

- [ ] **Step 3: 创建 PaginationBar 组件**

创建 `frontend/src/components/PaginationBar.vue`:

```vue
<template>
  <div class="pagination-bar">
    <span class="total-info">共 {{ total }} 条</span>
    <el-pagination
      v-model:current-page="currentPage"
      :page-size="pageSize"
      :total="total"
      layout="prev, pager, next"
      @current-change="handlePageChange"
      small
    />
    <el-button
      v-if="!allLoaded"
      size="small"
      type="primary"
      link
      @click="$emit('load-all')"
    >
      加载全部
    </el-button>
    <span v-else class="all-loaded-tip">已加载全部</span>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  total: { type: Number, default: 0 },
  pageSize: { type: Number, default: 10 },
  allLoaded: { type: Boolean, default: false },
})

const emit = defineEmits(['page-change', 'load-all'])
const currentPage = ref(1)

function handlePageChange(page) {
  currentPage.value = page
  emit('page-change', (page - 1) * props.pageSize)
}

watch(() => props.total, () => {
  currentPage.value = 1
})
</script>

<style scoped>
.pagination-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 24px;
  border-top: 1px solid #eee;
}

.total-info {
  color: #999;
  font-size: 13px;
}

.all-loaded-tip {
  color: #999;
  font-size: 12px;
}
</style>
```

- [ ] **Step 4: 创建 DataView 容器组件**

创建 `frontend/src/components/DataView.vue`:

```vue
<template>
  <div class="data-view" v-if="filePath">
    <Toolbar
      :fields="schema.fields"
      @search="handleSearch"
      @save-as="showSaveAsDialog = true"
    />
    <DataTable
      :rows="rows"
      :schema="schema"
      :offset="offset"
      @row-click="handleRowClick"
    />
    <PaginationBar
      :total="total"
      :page-size="pageSize"
      :all-loaded="allLoaded"
      @page-change="handlePageChange"
      @load-all="handleLoadAll"
    />
    <DetailDrawer
      v-model:visible="drawerVisible"
      :row="selectedRow"
      :row-index="selectedRowIndex"
      :schema="schema"
      :file-path="filePath"
      @saved="reloadCurrentPage"
      @deleted="reloadCurrentPage"
    />
    <el-dialog v-model="showSaveAsDialog" title="另存为" width="500px">
      <el-input v-model="saveAsPath" placeholder="输入目标文件路径" />
      <template #footer>
        <el-button @click="showSaveAsDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveAs">确定</el-button>
      </template>
    </el-dialog>
  </div>
  <div v-else class="empty-state">
    <p>请在左侧选择一个文件</p>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import Toolbar from './Toolbar.vue'
import DataTable from './DataTable.vue'
import PaginationBar from './PaginationBar.vue'
import DetailDrawer from './DetailDrawer.vue'
import { readFile, readFileAll, searchFile, saveAs } from '../api'

const props = defineProps({
  filePath: { type: String, default: '' },
})

const rows = ref([])
const schema = ref({ fields: [] })
const total = ref(0)
const offset = ref(0)
const pageSize = 10
const allLoaded = ref(false)

const drawerVisible = ref(false)
const selectedRow = ref(null)
const selectedRowIndex = ref(0)

const showSaveAsDialog = ref(false)
const saveAsPath = ref('')

async function loadData(newOffset = 0) {
  if (!props.filePath) return
  const { data } = await readFile(props.filePath, newOffset, pageSize)
  rows.value = data.rows
  total.value = data.total
  schema.value = data.schema
  offset.value = newOffset
  allLoaded.value = false
}

async function handleLoadAll() {
  const { data } = await readFileAll(props.filePath)
  rows.value = data.rows
  total.value = data.total
  schema.value = data.schema
  offset.value = 0
  allLoaded.value = true
}

async function handlePageChange(newOffset) {
  await loadData(newOffset)
}

async function handleSearch({ keyword, field }) {
  if (!keyword) {
    await loadData(0)
    return
  }
  const { data } = await searchFile(props.filePath, keyword, field)
  rows.value = data.results.map((r) => r.data)
  total.value = data.count
  offset.value = 0
  allLoaded.value = true
}

function handleRowClick({ row, index }) {
  selectedRow.value = row
  selectedRowIndex.value = index
  drawerVisible.value = true
}

async function reloadCurrentPage() {
  await loadData(offset.value)
}

async function handleSaveAs() {
  if (!saveAsPath.value.trim()) return
  await saveAs(props.filePath, saveAsPath.value.trim())
  ElMessage.success('另存为成功')
  showSaveAsDialog.value = false
  saveAsPath.value = ''
}

watch(() => props.filePath, () => {
  if (props.filePath) loadData(0)
})
</script>

<style scoped>
.data-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 15px;
}
</style>
```

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/
git commit -m "feat: DataView、DataTable、Toolbar、PaginationBar 组件"
```

---

### Task 9: DetailDrawer 和智能渲染组件

**文件：**
- 创建: `frontend/src/components/DetailDrawer.vue`
- 创建: `frontend/src/renderers/ConversationView.vue`
- 创建: `frontend/src/renderers/PreferenceView.vue`
- 创建: `frontend/src/renderers/InstructionView.vue`
- 创建: `frontend/src/renderers/JsonTreeView.vue`
- 创建: `frontend/src/renderers/EditorView.vue`

- [ ] **Step 1: 创建 ConversationView 渲染器**

创建 `frontend/src/renderers/ConversationView.vue`:

```vue
<template>
  <div class="conversation-view">
    <div
      v-for="(msg, i) in messages"
      :key="i"
      class="message-bubble"
      :class="'role-' + msg.role"
    >
      <div class="role-label">{{ msg.role }}</div>
      <div class="content">{{ msg.content }}</div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  messages: { type: Array, default: () => [] },
})
</script>

<style scoped>
.conversation-view {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-bubble {
  border-radius: 8px;
  padding: 12px 16px;
}

.role-label {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 6px;
  text-transform: uppercase;
}

.role-system {
  background: #f5f5f5;
}
.role-system .role-label { color: #999; }

.role-user {
  background: #f0f9eb;
}
.role-user .role-label { color: #67c23a; }

.role-assistant {
  background: #ecf5ff;
}
.role-assistant .role-label { color: #409eff; }

.content {
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
```

- [ ] **Step 2: 创建 PreferenceView 渲染器**

创建 `frontend/src/renderers/PreferenceView.vue`:

```vue
<template>
  <div class="preference-view">
    <div class="pref-column chosen">
      <div class="pref-label">✅ Chosen</div>
      <div class="pref-content">{{ formatValue(data.chosen) }}</div>
    </div>
    <div class="pref-column rejected">
      <div class="pref-label">❌ Rejected</div>
      <div class="pref-content">{{ formatValue(data.rejected) }}</div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  data: { type: Object, default: () => ({}) },
})

function formatValue(val) {
  if (typeof val === 'string') return val
  return JSON.stringify(val, null, 2)
}
</script>

<style scoped>
.preference-view {
  display: flex;
  gap: 16px;
}

.pref-column {
  flex: 1;
  border-radius: 8px;
  padding: 16px;
}

.chosen {
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
}

.rejected {
  background: #fef0f0;
  border: 1px solid #fde2e2;
}

.pref-label {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
}

.pref-content {
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
```

- [ ] **Step 3: 创建 InstructionView 渲染器**

创建 `frontend/src/renderers/InstructionView.vue`:

```vue
<template>
  <div class="instruction-view">
    <div class="section">
      <div class="section-label">Instruction</div>
      <div class="section-content">{{ data.instruction }}</div>
    </div>
    <div class="section" v-if="data.input">
      <div class="section-label">Input</div>
      <div class="section-content">{{ data.input }}</div>
    </div>
    <div class="section">
      <div class="section-label">Output</div>
      <div class="section-content">{{ data.output }}</div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  data: { type: Object, default: () => ({}) },
})
</script>

<style scoped>
.instruction-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section {
  background: #f7f8fa;
  border-radius: 8px;
  padding: 16px;
}

.section-label {
  font-size: 12px;
  font-weight: 600;
  color: #999;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.section-content {
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
```

- [ ] **Step 4: 创建 JsonTreeView 渲染器**

创建 `frontend/src/renderers/JsonTreeView.vue`:

```vue
<template>
  <div class="json-tree-view">
    <vue-json-pretty :data="data" :deep="3" :show-line="false" />
  </div>
</template>

<script setup>
import VueJsonPretty from 'vue-json-pretty'
import 'vue-json-pretty/lib/styles.css'

const props = defineProps({
  data: { type: [Object, Array, String, Number], default: null },
})
</script>

<style scoped>
.json-tree-view {
  padding: 8px;
  font-size: 13px;
}
</style>
```

- [ ] **Step 5: 创建 EditorView 渲染器**

创建 `frontend/src/renderers/EditorView.vue`:

```vue
<template>
  <div class="editor-view">
    <el-input
      v-model="jsonText"
      type="textarea"
      :rows="20"
      class="json-editor"
      spellcheck="false"
    />
    <div v-if="parseError" class="error-tip">{{ parseError }}</div>
    <div class="editor-actions">
      <el-button type="primary" @click="handleSave" :disabled="!!parseError">
        保存
      </el-button>
      <el-button @click="handleSaveAs" :disabled="!!parseError">
        另存为
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  data: { type: Object, default: null },
})

const emit = defineEmits(['save', 'save-as'])

const jsonText = ref('')

watch(() => props.data, (val) => {
  jsonText.value = JSON.stringify(val, null, 2)
}, { immediate: true })

const parseError = computed(() => {
  try {
    JSON.parse(jsonText.value)
    return null
  } catch (e) {
    return 'JSON 格式错误: ' + e.message
  }
})

function handleSave() {
  const parsed = JSON.parse(jsonText.value)
  emit('save', parsed)
}

function handleSaveAs() {
  const parsed = JSON.parse(jsonText.value)
  emit('save-as', parsed)
}
</script>

<style scoped>
.editor-view {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.json-editor :deep(textarea) {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.error-tip {
  color: #f56c6c;
  font-size: 12px;
}

.editor-actions {
  display: flex;
  gap: 8px;
}
</style>
```

- [ ] **Step 6: 创建 DetailDrawer 组件**

创建 `frontend/src/components/DetailDrawer.vue`:

```vue
<template>
  <el-drawer
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="数据详情"
    size="50%"
    :destroy-on-close="false"
  >
    <template v-if="row">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="智能视图" name="smart">
          <ConversationView
            v-if="detectedPattern === 'conversation'"
            :messages="row.messages"
          />
          <PreferenceView
            v-else-if="detectedPattern === 'preference'"
            :data="row"
          />
          <InstructionView
            v-else-if="detectedPattern === 'instruction'"
            :data="row"
          />
          <JsonTreeView v-else :data="row" />
        </el-tab-pane>
        <el-tab-pane label="原始 JSON" name="json">
          <JsonTreeView :data="row" />
        </el-tab-pane>
        <el-tab-pane label="编辑" name="edit">
          <EditorView
            :data="row"
            @save="handleSave"
            @save-as="handleSaveAs"
          />
        </el-tab-pane>
      </el-tabs>
    </template>
  </el-drawer>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ConversationView from '../renderers/ConversationView.vue'
import PreferenceView from '../renderers/PreferenceView.vue'
import InstructionView from '../renderers/InstructionView.vue'
import JsonTreeView from '../renderers/JsonTreeView.vue'
import EditorView from '../renderers/EditorView.vue'
import { updateRow, saveAs } from '../api'

const props = defineProps({
  visible: { type: Boolean, default: false },
  row: { type: Object, default: null },
  rowIndex: { type: Number, default: 0 },
  schema: { type: Object, default: () => ({ fields: [] }) },
  filePath: { type: String, default: '' },
})

const emit = defineEmits(['update:visible', 'saved', 'deleted'])

const activeTab = ref('smart')

const detectedPattern = computed(() => {
  if (!props.schema?.fields) return null
  for (const field of props.schema.fields) {
    if (field.pattern) return field.pattern
  }
  return null
})

async function handleSave(data) {
  await updateRow(props.filePath, props.rowIndex, data)
  ElMessage.success('保存成功')
  emit('saved')
}

async function handleSaveAs(data) {
  const { value: targetPath } = await ElMessageBox.prompt('输入目标文件路径', '另存为', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
  })
  if (targetPath) {
    // 先更新当前行，再另存整个文件
    await updateRow(props.filePath, props.rowIndex, data)
    await saveAs(props.filePath, targetPath)
    ElMessage.success('另存为成功')
  }
}
</script>
```

- [ ] **Step 7: 安装 @element-plus/icons-vue 依赖**

```bash
cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool/frontend && npm install @element-plus/icons-vue
```

- [ ] **Step 8: 验证前端完整运行**

同时启动后端和前端，完整测试：

1. 输入路径 → 文件树显示
2. 点击文件 → 表格显示前 10 条
3. 点击行 → 抽屉弹出，智能视图正确渲染
4. 分页翻页正常
5. 搜索返回结果

- [ ] **Step 9: 提交**

```bash
git add frontend/src/
git commit -m "feat: DetailDrawer 抽屉面板和全部智能渲染组件"
```

---

### Task 10: 生产部署 & 静态文件服务

**文件：**
- 修改: `backend/app.py`
- 修改: `main.py`

- [ ] **Step 1: 修改 app.py 添加静态文件服务**

修改 `backend/app.py`:

```python
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.routers import scan, file

def create_app() -> FastAPI:
    app = FastAPI(title="LLM 训练数据查看器")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(scan.router)
    app.include_router(file.router)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    # 生产环境：serve 前端构建产物
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.isdir(static_dir):
        from fastapi.responses import FileResponse

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            file_path = os.path.join(static_dir, full_path)
            if os.path.isfile(file_path):
                return FileResponse(file_path)
            return FileResponse(os.path.join(static_dir, "index.html"))

        app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")

    return app
```

- [ ] **Step 2: 构建前端**

```bash
cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool/frontend && npm run build
```

预期: 输出到 `backend/static/` 目录

- [ ] **Step 3: 测试生产模式**

```bash
cd /Users/liangyuanzhi/PycharmProjects/LLM_Label_Tool && python main.py --port 8000
```

打开 http://localhost:8000，应该能看到完整的前端页面，所有功能正常工作。

- [ ] **Step 4: 运行全部后端测试**

```bash
python -m pytest tests/ -v
```

预期: 全部通过

- [ ] **Step 5: 提交**

```bash
git add backend/app.py backend/static/ main.py
git commit -m "feat: 生产部署，FastAPI serve 前端静态文件"
```

---

### Task 11: 更新项目文档

**文件：**
- 修改: `CLAUDE.md`

- [ ] **Step 1: 更新 CLAUDE.md**

覆盖 `CLAUDE.md`:

```markdown
# CLAUDE.md

本文件为 Claude Code 在此代码仓库中工作时提供指导。

## 项目概述

LLM 训练数据查看器 — 本地部署的 Web 工具，用于浏览、查看、搜索和编辑 JSON/JSONL 格式的训练数据。

## 技术栈

- 后端: Python FastAPI
- 前端: Vue 3 + Vite + Element Plus
- 数据渲染: vue-json-pretty

## 运行项目

### 开发环境

终端 1 — 后端:
\`\`\`bash
pip install -r requirements.txt
python main.py --port 8000
\`\`\`

终端 2 — 前端:
\`\`\`bash
cd frontend
npm install
npm run dev
\`\`\`

### 生产环境

\`\`\`bash
cd frontend && npm run build
python main.py --port 8000
\`\`\`

打开 http://localhost:8000

## 运行测试

\`\`\`bash
pip install -r requirements.txt
python -m pytest tests/ -v
\`\`\`

## 项目结构

- `main.py` — 入口文件
- `backend/` — FastAPI 后端（路由、服务、模型）
- `frontend/` — Vue 3 前端
- `tests/` — 后端测试
- `docs/` — 设计文档和计划
\`\`\`
```

- [ ] **Step 2: 提交**

```bash
git add CLAUDE.md
git commit -m "docs: 更新 CLAUDE.md 项目文档"
```
