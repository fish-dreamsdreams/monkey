# 三国游戏内容编辑器

Phase 12：项目导入导出（客户端可读包、schema 与 checksum 校验）。

编辑器只负责创建、编辑、校验、保存内容数据。战斗、AI、动画留给未来游戏客户端。

## 设计要点

- 工作库：MySQL 8（SQLAlchemy 2 异步）
- `POST /projects/{id}/export` 必须先通过 ValidationEngine；失败 409 `export_blocked`
- `POST /projects/import` 核 schema_version 与分区 SHA-256，导入为新项目并重映射 ID
- 冻结目录：`var/projects/{id}/exports/v{content_version}/`（含 manifest.json）
- 不含 `quests.json` / `timeline.json`（模块尚未实现）
- 数据包 schema `1.11.0`，API `0.12.0`；无新表

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

## 当前验收

1. `GET /api/v1/meta` 中 `schema_version` 为 `1.11.0`，`alembic_script_head` 仍为 `0010_phase10`
2. 空项目可导出；残缺剧情导出 409
3. 人物可导出再导入，新项目中仍能列出
4. 篡改 checksum 或未知 schema 拒绝导入
