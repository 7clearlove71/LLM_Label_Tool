# 请求工具升级：Postman-lite 模型 设计文档

日期：2026-06-10
状态：已确认，待实现

## 背景

请求工具（类 Postman 的本地 HTTP 调试工具）当前为「draft（编辑区自动存）+ samples（已保存快照）」双轨模型。存在三个缺口：

1. curl 导入只会填进编辑区，不会落为左侧持久化样例。
2. 手动新建样例没有入口（只能「先编辑再另存为」）。
3. （现状已支持删除，本轮保留并加二次确认。）

目标：将交互范式收敛为 Postman-lite —— 编辑区始终绑定一个当前样例，改动自动保存；所有「创建请求」的入口都直接产生持久化样例。

## 现状架构（改造前）

- 后端：`backend/models.py`（`RequestSpec` / `RequestSample` / `RequestStore`）、`backend/services/request_store.py`（全量原子读写 `requests.json`）、`backend/routers/request.py`（GET/PUT `/api/requests`、send、parse-curl、to-curl）。
- 前端：`RequestModule.vue`（编排）、`components/request/` 下 `SampleList` / `RequestBuilder` / `ResponseView` / `CurlImportDialog` / `KeyValueEditor` / `BodyEditor`。
- 持久化：前端防抖整体 PUT `/api/requests`，后端原子写 + 损坏文件兜底。

## 目标交互模型

### 编辑区始终绑定当前样例
- 任何 spec 改动经 500ms 防抖**自动写回当前选中样例**（`samples[i].request`），复用现有「串行化 persist 链 + 失败回滚」。
- 取消独立 `draft` 概念。
- 持久化新增 `active_id`，重开页面恢复上次选中样例（`active_id` 失效时回退到第一个样例或空状态）。

### draft 迁移（一次性，前端 onMounted）
- 加载 store 后，若 `data.draft` 存在且非空（判定：method 非默认或 url 非空或任一集合非空），将其转为一个样例「未命名请求」追加到 `samples`，并选中。
- 迁移后不再发送 `draft` 字段（前端 persist 只发 `{ samples, active_id }`）。

## 三个创建入口（都产生持久化样例）

1. **+新建**（左侧顶部）：创建空白样例，名「未命名请求」，立即入库并选中。
2. **导入 curl**（左侧顶部）：解析成功后**新建一个样例**，名从 URL 生成（`new URL(url)` 的 `host + pathname`，去掉末尾斜杠；解析失败或 URL 为空则「导入的请求」），立即入库并选中。
3. **克隆**（样例行 hover）：深拷贝当前行为新样例，名「原名 副本」，立即入库并选中。

所有新建/导入/克隆均生成唯一 id：`String(Date.now()) + '-' + Math.random().toString(36).slice(2,6)`，避免快速操作 id 碰撞。

## 组件改动

### SampleList.vue
- 顶部 header 增两个动作：`+新建`、`导入curl`（发 `new` / `import-curl` 事件）。
- 每行 hover 操作增 `克隆`（发 `clone`，连同 sample）；保留 `改名` `删除`。
- 删除前 `ElMessageBox.confirm` 二次确认。

### RequestBuilder.vue
- 去掉「另存为样例」「更新当前样例」「导入curl」三个按钮及对应 emit。
- 工具行只留「复制为 curl」。
- 顶部新增轻量保存状态指示：`保存中…` / `已保存`（由父组件经 prop 传入 `saveState`：`'saving' | 'saved' | ''`）。
- 当无当前样例时（空状态），主区不渲染 Builder（见下）。

### RequestModule.vue（编排重写）
- 状态：`store = { samples }`、`spec`、`activeId`、`saveState`。
- onMounted：拉取 store → draft 迁移 → 恢复 `active_id`（有效则选中并载入其 request；否则若有样例选第一个；否则空状态）。
- `onSpecChange`：更新 `spec`，写回当前样例 `request`，置 `saveState='saving'`，防抖 persist；成功置 `'saved'`，失败回滚并提示。
- `new()`：建空白样例并选中。
- `onCurlImported(parsed)`：建样例（URL 生成名）并选中。
- `cloneSample(s)`：深拷贝建样例并选中。
- `loadSample` / `renameSample` / `deleteSample`：保留现有回滚逻辑；删除后自动选中第一个或回空状态。
- persist 只发 `{ samples, active_id: activeId }`。

### 空状态
- 无样例时主区显示空状态卡片，含 `新建请求` / `导入curl` 两个按钮。
- 删除当前选中后：有剩余样例则选中第一个，否则回空状态。

## 后端改动

### models.py
- `RequestStore` 增 `active_id: Optional[str] = None`；`draft: Optional[RequestSpec] = None` 保留（仅向后兼容旧文件加载，前端不再写入）。

### request_store.py / routers/request.py
- 无逻辑改动（仍全量原子读写、PUT 回存）。`active_id` 随 `RequestStore` 自动序列化。

## 数据流

```
用户操作（新建/导入/克隆/编辑/删除/选中）
  → RequestModule 更新 store.samples / activeId（乐观写）
  → 防抖 / 立即调用 persist()
  → PUT /api/requests { samples, active_id }
  → save_store 原子写 requests.json
  → 失败：回滚乐观写 + ElMessage 报错
```

## 错误处理
- 沿用现有：persist 串行链避免并发覆盖；每个变更失败回滚对应乐观写并提示。
- 损坏 `requests.json`：后端已有「备份 .corrupt 后返回空」兜底。
- curl 解析失败：弹窗内提示（现状已有），不产生样例。

## 测试
- 后端 pytest：
  - `RequestStore` 含 `active_id` 的序列化/反序列化往返。
  - 旧文件含 `draft`、无 `active_id` 仍能正常 `load_store`（向后兼容）。
  - save→load 往返保留 `active_id`。
- 前端无测试栈（项目仅 pytest），UI 行为走手动验证：
  - 导入 curl 后左侧出现并选中新样例；
  - +新建生成空白样例；克隆生成「副本」；
  - 编辑后刷新页面恢复内容与选中；
  - 删除当前样例后选中切换 / 空状态；
  - 旧 draft 迁移为样例。

## 不做（YAGNI）
鉴权助手、样例分组/文件夹、请求历史、变量/环境替换 —— 本轮不实现。
