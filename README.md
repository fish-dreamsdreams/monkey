# 三国游戏内容编辑器

Phase 10：资源/模型管理（路径存在性、人物绑定模型）。

编辑器只负责创建、编辑、校验、保存内容数据。战斗、AI、动画留给未来游戏客户端。

## 设计要点

- 工作库：MySQL 8（SQLAlchemy 2 异步）
- 资源只存相对路径、类型、checksum；人物通过 `portrait_asset_id` / `model_asset_id` 引用，**不**把裸路径写进人物表
- 登记时文件必须存在于项目 `assets` 下；禁止 `..` 与绝对路径
- 模型资源带 `ModelAsset` 扩展（格式/LOD），不加载网格、不播放动画
- 主键前缀：`res_` 资源，`mas_` 模型扩展

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

1. `GET /api/v1/meta` 中 `schema_version` 为 `1.9.0`，`alembic_script_head` 为 `0010_phase10`
2. 登记刘备头像：相对路径存在且 checksum 匹配
3. `../` 或绝对路径返回 400
4. 把头像/模型绑到刘备后，人物详情 `presentation` 只有资源 ID，没有磁盘绝对路径
5. 不能把模型资源当头像绑定

## 测试

```powershell
pytest -q
```

测试使用内存 SQLite，不要求本机 MySQL 正在运行。`db upgrade` 仍需要 MySQL。

## 当前阶段不做

跨实体校验引擎、项目导入导出、React 界面、战斗结算、3D 预览。
