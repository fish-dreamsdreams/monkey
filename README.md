# 三国游戏内容编辑器

Phase 3：人物史料来源（正史 / 演义 / 游戏设定分层）。

编辑器只负责创建、编辑、校验、保存内容数据。战斗、AI、动画留给未来游戏客户端。

## 设计要点

- 工作库：MySQL 8（SQLAlchemy 2 异步）
- 人物分栏：`base` 身份、`historical` 史实、`game` 游戏数值
- 史料目录按项目预置：`三国志`（正史）、`三国演义`（文学演义）等
- 引文必须声明 `bound_layer`：`historical` | `literary` | `game`
- 《三国演义》不能挂到 `historical` 层，也不能登记为正史
- 主键前缀：`prj_` / `chr_` / `tag_` / `src_` / `cit_`
- 错误响应统一为 `{ data, error, meta }`

## 环境要求

- Python 3.12+（类型与依赖按 3.12 声明）
- MySQL 8（本地可用 Docker）

当前若本机只有 Python 3.11，测试仍可运行，但请尽快安装 3.12 以符合项目约束。

## 启动 MySQL

```powershell
docker compose up -d mysql
copy .env.example .env
```

## 安装与迁移

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m backend.cli db upgrade
python -m backend.cli db check
```

不要在应用启动时自动 migrate。先 `upgrade` 再启动 API。

## 运行 API

```powershell
uvicorn backend.main:app --reload --port 8000
```

打开 Swagger：http://127.0.0.1:8000/docs

元信息：`GET /api/v1/meta`、`GET /health`

## 验证

1. `GET /api/v1/meta` 中 `schema_version` 为 `1.2.0`，`alembic_script_head` 为 `0003_phase3`
2. 创建项目后 `GET /api/v1/projects/{id}/sources` 能看到 `sanguozhi` 与 `sanguoyanyi`
3. 为刘备挂 `sanguozhi` + `historical` 成功
4. 为刘备挂 `sanguoyanyi` + `historical` 返回 400
5. 为刘备挂 `sanguoyanyi` + `literary` 成功
6. 新增来源名为「三国演义…」且类型为正史，返回 400

## 测试

```powershell
pytest -q
```

测试使用内存 SQLite，不要求本机 MySQL 正在运行。`db upgrade` 仍需要 MySQL。

## 当前阶段不做

人物关系、技能、城池、势力、地图、事件、剧情、资源管理、完整导入导出、React 界面。
