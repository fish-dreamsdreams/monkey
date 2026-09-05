# 三国游戏内容编辑器

Phase 4：人物关系（类型、时段、双向一致性）。

编辑器只负责创建、编辑、校验、保存内容数据。战斗、AI、动画留给未来游戏客户端。

## 设计要点

- 工作库：MySQL 8（SQLAlchemy 2 异步）
- 人物分栏：`base` / `historical` / `game`；演义不得写入史实栏
- 关系是有向边：`from_character` → `to_character`
- 对称类型（血缘、婚姻、结义、仇敌、同盟）自动写反向边
- 不对称类型（君臣、主从、师徒）：`from` 为上位（君/主/师）
- 同一对人物、同一类型，时段重叠则拒绝
- 主键前缀：`prj_` / `chr_` / `src_` / `cit_` / `rel_`

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

1. `GET /api/v1/meta` 中 `schema_version` 为 `1.3.0`，`alembic_script_head` 为 `0004_phase4`
2. 刘备 → 关羽 `sworn` 后，关羽的关系图也能看到刘备
3. 同一对、同一类型、年份重叠 → 409
4. 不同时段的两段结义可以并存
5. 刘备 → 诸葛亮 `ruler_subject` 后，诸葛亮侧为 `incoming`
6. 人物不能与自己建立关系

## 测试

```powershell
pytest -q
```

测试使用内存 SQLite，不要求本机 MySQL 正在运行。`db upgrade` 仍需要 MySQL。

## 当前阶段不做

技能、城池、势力、地图、事件、剧情、资源管理、完整导入导出、React 界面。
