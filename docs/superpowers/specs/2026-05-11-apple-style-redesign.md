# Apple 风格前端重设计

## 概述

将 LLM 训练数据查看器的前端界面从当前的 Element Plus 默认样式，全面改造为遵循 `frontend/DESIGN.md` 中定义的 Apple 设计规范。功能逻辑完全不变，仅重写视觉层。

**策略：** 保留 Element Plus 组件库，通过 CSS 变量覆盖 + scoped 样式深度定制其外观。布局保持工具型应用形态（侧边栏 + 内容区 + 详情抽屉）。

## 设计 Token 映射

所有视觉属性来源于 DESIGN.md，以下是本项目使用的核心 token：

### 颜色

| 用途 | Token | 值 |
|------|-------|----|
| 主交互色 | `--apple-primary` | #0066cc |
| 主色 hover | `--apple-primary-focus` | #0071e3 |
| 暗底链接色 | `--apple-primary-on-dark` | #2997ff |
| 文字色 | `--apple-ink` | #1d1d1f |
| 弱文字色 | `--apple-ink-muted-80` | #333333 |
| 次弱文字色 | `--apple-ink-muted-48` | #7a7a7a |
| 白色画布 | `--apple-canvas` | #ffffff |
| 米白画布 | `--apple-canvas-parchment` | #f5f5f7 |
| 珍珠白按钮底 | `--apple-surface-pearl` | #fafafc |
| 纯黑（导航栏） | `--apple-surface-black` | #000000 |
| 白色文字（暗底） | `--apple-on-dark` | #ffffff |
| 柔分隔线 | `--apple-divider-soft` | #f0f0f0 |
| 细线边框 | `--apple-hairline` | #e0e0e0 |

### 字体

| Token | 字号 | 字重 | 行高 | 字距 | 用途 |
|-------|------|------|------|------|------|
| `--typo-tagline` | 21px | 600 | 1.19 | 0.231px | 侧边栏标题 |
| `--typo-body-strong` | 17px | 600 | 1.24 | -0.374px | 强调文字 |
| `--typo-body` | 17px | 400 | 1.47 | -0.374px | 正文 |
| `--typo-caption` | 14px | 400 | 1.43 | -0.224px | 次要说明 |
| `--typo-caption-strong` | 14px | 600 | 1.29 | -0.224px | 强调说明 |
| `--typo-button-utility` | 14px | 400 | 1.29 | -0.224px | 工具按钮 |
| `--typo-fine-print` | 12px | 400 | 1.0 | -0.12px | 小字 |
| `--typo-nav-link` | 12px | 400 | 1.0 | -0.12px | 导航项 |

字体栈统一为：`system-ui, -apple-system, BlinkMacSystemFont, sans-serif`。

### 圆角

| Token | 值 | 用途 |
|-------|----|------|
| `--rounded-sm` | 8px | 工具按钮、消息气泡 |
| `--rounded-md` | 11px | Pearl 胶囊按钮 |
| `--rounded-lg` | 18px | 数据卡片 |
| `--rounded-pill` | 9999px | 主按钮、搜索输入框、书签标签 |

### 间距

| Token | 值 | 用途 |
|-------|----|------|
| `--space-xxs` | 4px | 微间距 |
| `--space-xs` | 8px | 紧凑间距 |
| `--space-sm` | 12px | 小间距 |
| `--space-md` | 17px | 标准间距 |
| `--space-lg` | 24px | 大间距 |
| `--space-xl` | 32px | 特大间距 |

## 各组件设计

### 1. App.vue — 全局布局

- **body** 字体切换为 SF Pro 字体栈，正文 17px
- **顶部导航栏：** 单层，高度 44px，背景 `--apple-surface-black`，标题白色 `--typo-nav-link` 大小但 font-weight 600，右侧放"另存为"等全局操作按钮（文字链接形式，白色）
- **侧边栏：** 背景 `--apple-canvas-parchment`，右边框改为 `--apple-hairline`
- **侧边栏可拖拽调整宽度：** 默认 260px，范围 180px–480px。右边缘放 4px 拖拽手柄，默认透明，hover 时显示 `--apple-primary` 蓝色条纹作为视觉反馈，光标 `col-resize`
- **主内容区：** 背景 `--apple-canvas`
- 移除全局的 drawer 动画禁用 CSS（改造后保留默认过渡或自定义平滑过渡）

### 2. PathInput.vue — 路径输入 + 书签

- **输入框：** 改为 pill 形（`--rounded-pill`），1px `rgba(0,0,0,0.08)` 边框，背景白色，高度 36px，内部 padding 0 16px
- **扫描按钮：** 从 el-button append 改为独立的 pill 形主按钮（`--apple-primary` 背景，白色文字），放在输入框下方
- **收藏星号：** 保持在输入框内右侧
- **书签标签：** 从 el-tag 改为自定义 pill 形标签。默认书签用 `--apple-primary` 蓝底白字，其他书签用白底 + hairline 边框。关闭按钮保留。
- **按压微交互：** 扫描按钮和书签标签按下时 `transform: scale(0.95)`

### 3. FileTree.vue — 文件树

- 覆盖 el-tree 样式：去除默认高亮背景，选中项改为 `rgba(0,102,204,0.08)` 浅蓝底 + `--rounded-sm` 圆角
- 节点字号 14px（`--typo-caption`），文件大小标注 12px 灰色
- hover 项背景 `--apple-canvas-parchment` 微调深一点
- 保留 📁📄 emoji 图标

### 4. Toolbar.vue — 搜索工具栏

- **搜索输入框：** pill 形（`--rounded-pill`），高度 36px，1px `rgba(0,0,0,0.08)` 边框，前置搜索图标灰色
- **字段选择器：** 覆盖 el-select 样式为 Pearl 胶囊风格 — 背景 `--apple-surface-pearl`，圆角 `--rounded-md`(11px)，字号 14px
- **搜索按钮：** pill 形主按钮，`--apple-primary` 背景
- **"另存为"按钮：** 移至顶部导航栏右侧（全局操作归导航栏管理）。如果 DataView 未加载文件则隐藏

### 5. DataTable.vue — 数据卡片列表

- **卡片容器：** 圆角 `--rounded-lg`(18px)，1px `--apple-hairline` 边框，padding 20px 24px，无阴影
- **卡片 hover：** 边框色变 `--apple-primary`，无 box-shadow（Apple 风格不给卡片加阴影）
- **卡片索引号：** `--apple-primary` 蓝色，`--typo-caption-strong`
- **操作提示：** "点击查看详情" 用 `--apple-ink-muted-48` 灰色
- **对话预览气泡：** 圆角 `--rounded-sm`(8px)，system 用 `--apple-canvas-parchment` 底，user 保持绿底，assistant 改为浅蓝底 `#f0f4ff`。role 标签全大写，11px，对应颜色
- **偏好预览：** 两列布局不变，chosen 绿底 / rejected 红底保留（语义色不被 Apple 设计替代）
- **指令预览：** section 背景改为 `--apple-canvas-parchment`，圆角 `--rounded-sm`
- **通用字段：** 字号 14px，field-name 灰色 `--apple-ink-muted-48`

### 6. PaginationBar.vue — 分页栏

- 覆盖 el-pagination 样式：页码按钮 `--rounded-sm` 圆角，当前页 `--apple-primary` 蓝底白字，非当前页 `--apple-surface-pearl` 底
- "共 N 条" 用 `--apple-ink-muted-48` 灰色，14px
- "加载全部" 用 `--apple-primary` 蓝色文字链接

### 7. DetailDrawer.vue — 详情抽屉

- 覆盖 el-drawer 样式：去除默认阴影，改为左边框 1px `--apple-hairline`
- 抽屉标题 "数据详情" 用 `--typo-tagline`（21px/600）
- 覆盖 el-tabs 样式：tab 文字 `--typo-caption`(14px)，激活态下划线改为 `--apple-primary` 蓝色，2px 粗

### 8. ConversationView.vue — 对话渲染

- 气泡圆角 `--rounded-sm`(8px)，padding 14px 18px
- role 标签 12px/600 全大写
- system: 背景 `--apple-canvas-parchment`，label 色 `--apple-ink-muted-48`
- user: 背景 `#f0f9eb` 保留（语义绿）
- assistant: 背景 `#f0f4ff`，label 色 `--apple-primary`
- 正文 `--typo-body`(17px/400/1.47)

### 9. PreferenceView.vue — 偏好渲染

- 两列布局，圆角 `--rounded-sm`(8px)
- chosen/rejected 的语义色保留
- 标签和正文字号对齐到 Apple body token

### 10. InstructionView.vue — 指令渲染

- section 背景 `--apple-canvas-parchment`，圆角 `--rounded-sm`
- label 改为 `--typo-fine-print`(12px/600)，颜色 `--apple-ink-muted-48`
- 正文 `--typo-body`

### 11. JsonTreeView.vue — JSON 树

- 字号改为 14px，与 Apple caption 对齐
- 无其他大改

### 12. EditorView.vue — 编辑器

- textarea 字体保持等宽（SF Mono, Consolas, monospace），字号 14px
- 保存按钮：pill 形主按钮 `--apple-primary`
- 另存为按钮：pill 形次级按钮（白底 + `--apple-primary` 文字 + 1px `--apple-primary` 边框）
- 错误提示保留红色

### 13. Element Plus 全局覆盖

在 `main.js` 或全局 CSS 中覆盖 Element Plus CSS 变量：
- `--el-color-primary` → `#0066cc`
- `--el-color-primary-light-3` → `#0071e3`
- `--el-border-radius-base` → `8px`
- `--el-font-size-base` → `17px`
- `--el-font-family` → SF Pro 字体栈
- `--el-border-color` → `#e0e0e0`
- `--el-border-color-light` → `#f0f0f0`
- `--el-fill-color-light` → `#f5f5f7`

## 不变的部分

- 所有 `<script setup>` 逻辑、props、emit、API 调用完全不动
- 组件文件结构不变（不新建/删除组件文件）
- `api/index.js` 不动
- `main.js` 仅增加 Element Plus CSS 变量覆盖
- `style.css` 将被清理，移除 Vite 默认模板样式，替换为 Apple token 定义

## 新增功能

- **侧边栏拖拽调整宽度：** 在 App.vue 中实现。侧边栏与主内容区之间放 4px 宽的拖拽手柄 div，通过 mousedown/mousemove/mouseup 事件控制侧边栏宽度。默认 260px，范围 180px–480px。拖拽手柄默认透明与边框融合，hover 时显示蓝色高亮。
