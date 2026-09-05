# 三国游戏内容编辑器

Phase 13：游戏客户端数据接口冻结（schema 版本与示例加载器）。

编辑器只负责创建、编辑、校验、保存内容数据。战斗、AI、动画留给未来游戏客户端。

## 设计要点

- 工作库：MySQL 8（SQLAlchemy 2 异步）
- 客户端只读 `packages/game-data-schema/frozen.json` 合同，不连接编辑器数据库
- 示例加载器：`game_data_loader.load_export_dir`，校验冻结 schema 与 checksum
- `GET /api/v1/client-schema` 返回冻结合同摘要
- 不含 `quests.json` / `timeline.json`；禁止把运行时存档写回工作库
- 数据包 schema `1.12.0`，API `0.13.0`；无新表

## 环境要求

- Python 3.12+（类型与依赖按 3.12 声明）
- MySQL 8（本地可用 Docker）

## 本地启动

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
copy .env.example .env
docker compose up -d mysql
alembic upgrade head
uvicorn backend.main:app --reload
```

另开终端启动前端：

```powershell
cd editor
npm install
npm run dev
```

浏览器打开 http://127.0.0.1:5173 。Vite 把 `/api` 与 `/health` 代理到 FastAPI。

## 当前验收

1. `GET /api/v1/meta` 中 `schema_version` 与 `frozen_client_schema_version` 均为 `1.12.0`，Alembic 仍为 `0010_phase10`
2. `GET /api/v1/client-schema` 列出冻结分区，且不含 quests/timeline
3. `data/sample-export` 可被 `game_data_loader` 加载出刘备
4. 编辑器导出目录可被同一加载器读取；错误 schema 或 checksum 拒绝加载
