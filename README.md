# 三国游戏内容编辑器

Phase 2：公共基础设施（Alembic CLI、统一错误、ID 规则、项目上下文）。

编辑器只负责创建、编辑、校验、保存内容数据。战斗、AI、动画留给未来游戏客户端。

## 设计要点

- 工作库：MySQL 8（SQLAlchemy 2 异步）
- 人物分栏：`base` 身份、`historical` 史实、`game` 游戏数值
- 主键带类型前缀：`prj_` / `chr_` / `tag_` ；业务 `code` 另计（如 `chr_liu_bei`、`han_end`）
- 所有内容 API 先解析项目上下文：ID 格式 → 项目存在 → schema 兼容
- 错误响应统一为 `{ data, error, meta }`
- 导出契约：`packages/game-data-schema/character.schema.json`

## 环境要求

- Python 3.12+（类型与依赖按 3.12 声明）
- MySQL 8（本地可用 Docker）

当前若本机只有 Python 3.11，测试仍可运行，但请尽快安装 3.12 以符合项目约束。

## 启动 MySQL

```powershell
docker compose up -d mysql
copy .env.example .env
```

手动创建数据库时请使用 `utf8mb4`：

```sql
CREATE DATABASE sanguo_editor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 安装与迁移

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m backend.cli db upgrade
python -m backend.cli db current
python -m backend.cli db check
```

等价写法：`.\scripts\db.ps1 upgrade`

不要在应用启动时自动 migrate。先 `upgrade` 再启动 API。

## 运行 API

```powershell
uvicorn backend.main:app --reload --port 8000
```

打开 Swagger：http://127.0.0.1:8000/docs

元信息：`GET /api/v1/meta`、`GET /health`

## 验证

1. `GET /api/v1/meta` 中 `schema_version` 为 `1.1.0`，`alembic_script_head` 为 `0002_phase2`
2. `POST /api/v1/projects` 返回 `id` 以 `prj_` 开头，可带 `code`
3. `GET /api/v1/projects/not-a-valid-id` 返回 400 / `invalid_id`
4. `PUT /api/v1/projects/{id}` 可改名称，不能改 code
5. 创建人物后 `id` 以 `chr_` 开头
6. `birth_year > death_year` 应 400；重复人物 code 应 409

## 测试

```powershell
pytest -q
```

测试使用内存 SQLite，不要求本机 MySQL 正在运行。`db upgrade` 仍需要 MySQL。

## 当前阶段不做

人物关系、技能、城池、势力、地图、事件、剧情、资源管理、完整导入导出、React 界面。
