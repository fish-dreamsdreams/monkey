# 三国游戏内容编辑器

Phase 1：项目初始化 + MySQL + SQLAlchemy + Pydantic + 人物管理。

编辑器只负责创建、编辑、校验、保存内容数据。战斗、AI、动画留给未来游戏客户端。

## 设计要点

- 工作库：MySQL 8（SQLAlchemy 2 异步）
- 人物分栏：`base` 身份、`historical` 史实、`game` 游戏数值
- 性格为结构化标签，不是一段文本
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
alembic upgrade head
```

## 运行 API

```powershell
uvicorn backend.main:app --reload --port 8000
```

打开 Swagger：http://127.0.0.1:8000/docs

## 验证人物功能

1. `POST /api/v1/projects` 创建项目（会写入 9 个系统性格标签）
2. `GET /api/v1/projects/{id}/personality-tags` 查看性格
3. `POST /api/v1/projects/{id}/characters` 创建人物，body 必须分 `base` / `historical` / `game`
4. 尝试 `birth_year > death_year`，应返回 400
5. 重复 `code` 应返回 409

刘备示例：

```json
{
  "base": {
    "code": "chr_liu_bei",
    "name": "刘备",
    "courtesy_name": "玄德",
    "gender": "male",
    "birth_year": 161,
    "death_year": 223,
    "birthplace": "涿郡涿县",
    "identity": "蜀汉开国皇帝"
  },
  "historical": {
    "biography": "东汉末年幽州涿郡人，蜀汉开国皇帝。"
  },
  "game": {
    "force": 72,
    "intelligence": 80,
    "politics": 85,
    "charisma": 95,
    "leadership": 86,
    "personality_tag_codes": ["benevolent", "ambitious"]
  }
}
```

## 测试

```powershell
pytest -q
```

测试使用内存 SQLite，不要求本机 MySQL 正在运行。

## Phase 1 不做

人物关系、技能、城池、势力、地图、事件、剧情、资源管理、完整导入导出、React 界面。
