# 三国游戏内容编辑器

Phase 9：剧情编辑器（节点图 + 环检测）。

编辑器只负责创建、编辑、校验、保存内容数据。战斗、AI、动画留给未来游戏客户端。

## 设计要点

- 工作库：MySQL 8（SQLAlchemy 2 异步）
- 剧情是游戏叙事层：可引用历史事件，**不**改写人物史实栏，**不**结算战斗
- 无条件 `next_nodes` 禁止成环；条件回边必须填写终止条件
- 必须恰好一个入口，且能到达至少一个结束节点
- `layer` 只能是 `literary` 或 `game`
- 主键前缀：`sty_` 剧情，`chp_` 章节，`snd_` 节点，`sed_` 边，`cho_` 选项

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

1. `GET /api/v1/meta` 中 `schema_version` 为 `1.8.0`，`alembic_script_head` 为 `0009_phase9`
2. 桃园结义：入口对白 → 选项 → 结束，图校验 `valid=true`
3. 无条件边 A→B→A 返回 400
4. 条件回边必须写终止条件
5. `historical_event` 节点必须引用已存在的事件；挂剧情不改人物 biography

## 测试

```powershell
pytest -q
```

测试使用内存 SQLite，不要求本机 MySQL 正在运行。`db upgrade` 仍需要 MySQL。

## 当前阶段不做

任务独立模块、时间线容器、资源管理、完整导入导出、React 界面、战斗结算。
