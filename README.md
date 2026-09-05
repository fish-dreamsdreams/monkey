# 三国游戏内容编辑器

Phase 7：2D 地图（地形网格 + 矢量地物 + 城池挂坐标）。

编辑器只负责创建、编辑、校验、保存内容数据。战斗、AI、动画留给未来游戏客户端。本阶段提供地图 **API**，不做 Canvas/SVG 画布。

## 设计要点

- 工作库：MySQL 8（SQLAlchemy 2 异步）
- 地形是**稀疏覆盖**：只存与默认地形不同的格子，按图层 `PATCH`，避免整图 JSON
- 区域 / 道路 / 河流 / 山脉是点列矢量，客户端解释绘制
- 城池通过 `map_id` + 格子坐标挂到地图；地图不直接拥有人物
- 主键前缀：`map_` 地图，`tcl_` 地形格，`mft_` 地物

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

1. `GET /api/v1/meta` 中 `schema_version` 为 `1.6.0`，`alembic_script_head` 为 `0007_phase7`
2. 创建 20×16 地图，不预填 320 个地块
3. `PATCH /maps/{id}/terrain` 只提交变更格
4. 添加长江（river 折线），把成都挂到格子上
5. 越界地块、两点山脉、同格两城会被拒绝

## 测试

```powershell
pytest -q
```

测试使用内存 SQLite，不要求本机 MySQL 正在运行。`db upgrade` 仍需要 MySQL。

## 当前阶段不做

Canvas 地图编辑器、历史事件、剧情、资源管理、完整导入导出、React 界面、战斗结算。
