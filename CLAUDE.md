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
```bash
pip install -r requirements.txt
python main.py --port 8000
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
python main.py --port 8000
```

打开 http://localhost:8000

## 运行测试

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

## 项目结构

- `main.py` — 入口文件
- `backend/` — FastAPI 后端（路由、服务、模型）
- `frontend/` — Vue 3 前端
- `tests/` — 后端测试
- `docs/` — 设计文档和计划
