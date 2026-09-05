# 三国游戏内容编辑器

Phase 8：历史事件（年/月/日、地点、参与者校验生卒）。

编辑器只负责创建、编辑、校验、保存内容数据。战斗、AI、动画留给未来游戏客户端。

## 设计要点

- 工作库：MySQL 8（SQLAlchemy 2 异步）
- 事件是编年记录：`consequences` 只是文本，**不**结算战斗或改游戏数值
- 参与人物必须活在事件当年；势力与地点城池必须当年仍存续
- `layer=historical` 不能引用《三国演义》；演义事件用 `layer=literary`
- 挂事件不会改写人物 `historical` 栏
- 主键前缀：`evt_` 事件，`evp_` 参与者，`evf_` 势力牵涉，`evs_` 引文

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

1. `GET /api/v1/meta` 中 `schema_version` 为 `1.7.0`，`alembic_script_head` 为 `0008_phase8`
2. 创建赤壁之战（208），刘备可参与
3. 刘备不能参与 230 年事件
4. 史实事件不能引用 `sanguoyanyi`；演义事件可以
5. 已毁城池不能作为事件地点

## 测试

```powershell
pytest -q
```

测试使用内存 SQLite，不要求本机 MySQL 正在运行。`db upgrade` 仍需要 MySQL。

## 当前阶段不做

剧情编辑器、时间线容器、资源管理、完整导入导出、React 界面、战斗结算。
