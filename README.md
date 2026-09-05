# 三国游戏内容编辑器

Phase 6：城池与势力（时序归属，势力由用户创建）。

编辑器只负责创建、编辑、校验、保存内容数据。战斗、AI、动画留给未来游戏客户端。

## 设计要点

- 工作库：MySQL 8（SQLAlchemy 2 异步）
- 城池分史实栏与游戏数值栏；**当前归属不入库**
- 势力由用户创建，**不预置魏蜀吴**
- 人物入势、城池归属都带起止年；同一时段一人不能两势、一城不能两属
- `GET /year-view?year=215` 派生该年城池 owner 与在势成员
- 主键前缀：`cty_` 城池，`fac_` 势力，`fmb_` 成员，`ftr_` 领土

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

1. `GET /api/v1/meta` 中 `schema_version` 为 `1.5.0`，`alembic_script_head` 为 `0006_phase6`
2. 新建项目后 `GET /factions` 为空
3. 创建成都与「左将军领」，领土 214–221；`at_year=208` 无 owner，`at_year=215` 有 owner
4. 刘备同时加入两个重叠时段势力 → 409
5. 一城同时两属 → 409

## 测试

```powershell
pytest -q
```

测试使用内存 SQLite，不要求本机 MySQL 正在运行。`db upgrade` 仍需要 MySQL。

## 当前阶段不做

地图编辑器、事件、剧情、资源管理、完整导入导出、React 界面、战斗结算。
