# LLM Training Data Viewer - Design Spec

## Overview

A local-deployment web tool for browsing, viewing, searching, and editing LLM training data in JSON/JSONL format. Designed for ML engineers who work with diverse training datasets (SFT, RL/preference, instruction-tuning, etc.).

## Core User Flow

1. User starts the server: `python main.py --port 8000`
2. Opens browser, enters a local folder path
3. Left panel shows file tree of all .json/.jsonl files under that folder
4. Click a file → right panel shows data table (default first 10 rows, with "Load All" option)
5. Click a row → right drawer panel opens with smart-rendered detail view
6. User can search, filter, edit, save, or export data

## Tech Stack

- **Backend**: Python FastAPI
- **Frontend**: Vue 3 + Vite + Element Plus
- **Data rendering**: vue-json-pretty (JSON tree), Monaco Editor or textarea (editing)
- **Deployment**: FastAPI serves built static files in production; Vite dev server + proxy in development. Single port, no extra dependencies.

## Architecture

```
┌──────────────────────────────────────────────┐
│              Vue 3 Frontend (SPA)            │
│  Element Plus + vue-json-pretty              │
│  Vite build, dev server + proxy              │
└──────────────┬───────────────────────────────┘
               │ HTTP REST API
┌──────────────▼───────────────────────────────┐
│           FastAPI Backend                     │
│  - Directory scan & file tree                │
│  - Line-based file reading & pagination      │
│  - Data editing & saving (overwrite/save-as) │
│  - Search & filtering                        │
└──────────────┬───────────────────────────────┘
               │ Direct file system read/write
┌──────────────▼───────────────────────────────┘
│          Local File System                    │
│  User-specified directory of JSON/JSONL files │
└──────────────────────────────────────────────┘
```

No database. All data is read from and written to local files directly.

## Layout

Classic two-panel layout:

- **Left panel**: File tree (collapsible sidebar)
- **Right panel**: Toolbar + Data table + Pagination
- **Detail drawer**: Slides in from right when a row is clicked

### Visual Style

White, minimal, premium feel:

- Main background: `#FFFFFF`, panels/cards: `#F7F8FA`
- Accent color: low-saturation indigo/blue-gray
- Text: `#333333` primary, `#999999` secondary
- Generous whitespace, thin divider lines, no decorative elements
- Conversation bubbles use soft pastel backgrounds per role (light blue, light green, light gray)

## File Reading Strategy

Both JSON and JSONL files follow the same convention: **one dict per line = one data entry**.

- **Default**: Read first 10 lines only (fast loading)
- **Load All**: User can click "Load All" button to load the entire file
- **Pagination**: offset/limit based on line numbers
- **Line count caching**: First open scans total line count and caches it
- File tree shows file name + row count + file size

## API Design

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scan` | POST | Input: folder path. Returns: file tree (recursive scan for .json/.jsonl) |
| `/api/file/read` | POST | Input: file path + offset (default 0) + limit (default 10). Returns: data rows + total count + schema |
| `/api/file/read-all` | POST | Input: file path. Returns: all data rows |
| `/api/file/update` | POST | Input: file path + row index + new data. Overwrites that line in original file |
| `/api/file/delete` | POST | Input: file path + row index. Removes that line from file |
| `/api/file/save-as` | POST | Input: source file path + target file path. Saves current data to new file |
| `/api/file/search` | POST | Input: file path + keyword + optional field name. Returns matching rows |

## Smart Schema Detection

On file read, the backend analyzes the first 10 rows to produce a schema describing each field:

```json
{
  "fields": [
    {"name": "id", "type": "number", "display": "column"},
    {"name": "messages", "type": "array<object>", "display": "detail",
     "pattern": "conversation",
     "children": [{"name": "role", "type": "string"}, {"name": "content", "type": "string"}]},
    {"name": "score", "type": "number", "display": "column"}
  ]
}
```

### Field Display Rules

| Field Type | Table Display | Drawer Display |
|-----------|---------------|----------------|
| Simple value (string/number/bool) | Direct column | Plain text |
| Short string (<100 chars) | Full text column | Plain text |
| Long string (>=100 chars) | Truncated column | Full text / Markdown block |
| Array with role/content objects | `[N items]` | **Conversation bubble cards** |
| Object with chosen/rejected | `{...}` | **Preference comparison** (side-by-side) |
| Object with instruction/input/output | `{...}` | **Instruction triplet** view |
| Generic array | `[N items]` | Expanded list |
| Generic object | `{N keys}` | JSON tree (vue-json-pretty) |

### Recognized Data Patterns

1. **Conversation** (`messages` array with `role`/`content` objects): Rendered as colored bubble cards
   - system: light gray background
   - user: light green background  
   - assistant: light blue background
2. **Preference/RL** (`chosen`/`rejected` fields): Side-by-side comparison panel
3. **Instruction** (`instruction`/`input`/`output` fields): Three-section layout
4. **Fallback**: JSON tree view (works for any structure)

### Drawer Tabs

Tabs are dynamically composed based on detected patterns:

- **Smart View** (always present): Auto-rendered based on detected pattern (conversation bubbles, preference comparison, instruction triplet, or JSON tree)
- **Raw JSON** (always present): Full JSON via vue-json-pretty, collapsible
- **Edit** (always present): Code editor for direct JSON editing, with "Save" (overwrite) and "Save As" buttons

## Frontend Component Structure

```
App.vue
├── PathInput              # Top bar: folder path input + scan button
├── FileTree               # Left panel: el-tree directory tree
│   └── Shows filename + row count + file size
├── DataView               # Right main area
│   ├── Toolbar            # Search box, field filter dropdown, save-as button
│   ├── DataTable          # Auto-detected columns from schema
│   │   └── Nested fields show summary, click row opens drawer
│   ├── Pagination         # Page nav + "Load All" button
│   └── DetailDrawer       # Right slide-in drawer
│       ├── Smart View     # Auto-rendered by detected pattern
│       ├── Raw JSON       # vue-json-pretty
│       └── Edit           # JSON editor + Save / Save As
```

## Search & Filter

- **Full-text search**: Keyword input, backend scans lines for matches, returns matching rows
- **Field filter**: Dropdown selects a field from schema, input matches against that field's value
- **Search result highlighting**: Matched text highlighted in results

## Edit & Save

- **Default action**: Save overwrites the original line in the source file
- **Save As**: Dialog to specify a new file path, writes all current data to new file
- **Delete**: Removes the selected row (line) from the file
- **Edit UI**: JSON editor in the drawer's Edit tab

## Startup

```bash
# Development
cd frontend && npm run dev    # Vite dev server on :5173
cd backend && uvicorn main:app --port 8000

# Production
cd frontend && npm run build  # Outputs to backend/static/
python main.py --port 8000    # FastAPI serves everything
```

Single command production start: `python main.py --port 8000`, then open `http://localhost:8000`.
