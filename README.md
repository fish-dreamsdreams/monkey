# 三国游戏内容编辑器

Phase 5：技能系统（定义 + 人物绑定，效果仅为数据）。

编辑器只负责创建、编辑、校验、保存内容数据。战斗、AI、动画留给未来游戏客户端。

## 设计要点

- 工作库：MySQL 8（SQLAlchemy 2 异步）
- 技能属于游戏层：`effects` 是 JSON payload，客户端解释执行
- 编辑器**不**实现伤害公式、冷却倒计时或脚本求值
- 演义技能用 `historical_basis.source_type = literary`，不得写进人物 `historical`
- 人物通过 `character_skills` 绑定技能与等级
- 主键前缀：`skl_` 技能，`csk_` 人物技能绑定

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

1. `GET /api/v1/meta` 中 `schema_version` 为 `1.4.0`，`alembic_script_head` 为 `0005_phase5`
2. 创建「空城计」，`historical_basis.source_type=literary`
3. 绑到刘备后，人物 `historical.biography` 不会出现该技能
4. `effects` 缺少 `modify_stat.stat` → 422
5. `type=eval_script` → 422
6. 同一人物重复绑定同一技能 → 409

## 测试

```powershell
pytest -q
```

测试使用内存 SQLite，不要求本机 MySQL 正在运行。`db upgrade` 仍需要 MySQL。

## 当前阶段不做

城池、势力、地图、事件、剧情、资源管理、完整导入导出、React 界面、战斗结算。
