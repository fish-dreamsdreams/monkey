# 三国游戏内容编辑器

Phase 11：跨实体数据校验引擎（时间线、易主、死循环）。

编辑器只负责创建、编辑、校验、保存内容数据。战斗、AI、动画留给未来游戏客户端。

## 设计要点

- 工作库：MySQL 8（SQLAlchemy 2 异步）
- `GET /projects/{id}/validation` 扫描全项目，写服务**不**反向依赖引擎
- 两种模式：`strict_historical`（默认）与 `game_narrative`
- 传说例外必须标注 `source_type`，且只在叙事模式下降为警告
- 城池归属时段不可重叠；剧情无条件边禁止成环
- 报告始终 200；`valid=false` 表示不能导出

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

## 验证

1. `GET /api/v1/meta` 中 `schema_version` 为 `1.10.0`，`alembic_script_head` 仍为 `0010_phase10`
2. 空项目校验 `valid=true`
3. 无结束节点的剧情草稿报告 `story_graph`
4. 同一城池重叠归属报告 `city_ownership`
5. 关羽卒后仍参与事件：严格模式 error，叙事模式且有演义来源则为 warning

## 测试

```powershell
pytest -q
```

测试使用内存 SQLite，不要求本机 MySQL 正在运行。`db upgrade` 仍需要 MySQL。

## 当前阶段不做

项目导入导出、React 界面、战斗结算、独立时间线/任务模块。
