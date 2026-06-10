# CLAUDE.md

本文件为 Claude Code 在此代码仓库中工作时提供指导。

## 项目概述

LLM 训练数据工具 — 本地部署的 Web 工具，采用顶部 Tab 模块化导航，包含两个模块：

- **查看器（Viewer）** — 浏览、查看、搜索和编辑 JSON/JSONL 格式的训练数据，支持书签、schema 自动识别与智能渲染。
- **请求工具（postwoman，Postman-lite）** — 构造并发送 HTTP 请求、curl 导入/导出、请求样例自动保存与管理。

## 技术栈

- 后端: Python FastAPI
- 前端: Vue 3 + Vite + Element Plus（顶部 Tab 模块化导航，Apple 风格 UI）
- 数据渲染: vue-json-pretty
- HTTP 请求发送: httpx

## 运行项目

### 开发环境

终端 1 — 后端:
```bash
pip install -r requirements.txt
python main.py --port 8002
```

终端 2 — 前端:
```bash
cd frontend
npm install
npm run dev
```

### 生产环境

```bash
cd frontend && npm run build
python main.py --port 8002
```

前端构建产物输出到 `backend/static/`，由 FastAPI 直接 serve（见 `frontend/vite.config.js` 的 `outDir`）。

打开 http://localhost:8002

## 运行测试

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

## 项目结构

- `main.py` — 入口文件（启动 uvicorn，默认端口 8002）
- `backend/` — FastAPI 后端
  - `app.py` — 应用装配（CORS、路由注册、生产环境 SPA serve）
  - `routers/` — 路由层：`scan` / `file` / `bookmark` / `request`
  - `services/` — 服务层：`scanner` / `reader` / `editor` / `searcher` / `schema` / `bookmark` / `request_store` / `http_client` / `curl_parser`
  - `models.py` — 数据模型
- `frontend/` — Vue 3 前端
  - `modules/` — 模块容器：`ViewerModule` / `RequestModule`，由 `App.vue` 顶部 Tab 切换
  - `components/` — 查看器组件（`DataView` / `DataTable` / `FileTree` / `Toolbar` 等）
  - `components/request/` — 请求工具组件（`RequestBuilder` / `SampleList` / `KeyValueEditor` / `BodyEditor` / `ResponseView` / `CurlImportDialog`）
  - `renderers/` — 数据智能渲染器（`SmartView` / `ConversationView` / `PreferenceView` / `InstructionView` / `EditorView` / `JsonTreeView`）
  - `api/index.js` — 后端 API 封装
- `tests/` — 后端测试（pytest）
- `docs/` — 设计文档和计划

## 数据文件

- `bookmarks.json` — 书签持久化（已纳入版本控制）
- `requests.json` — 请求工具样例/草稿持久化（已 gitignore，运行时由 `request_store` 原子写入）
