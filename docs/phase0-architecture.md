# Phase 0：三国游戏内容管理工具 — 系统总体架构设计

> 状态：技术选型与源码 Git 仓库已确认（不包含业务代码）  
> 范围：仅架构、边界、数据关系、MVP 与扩展路线  
> 约束：数据与游戏逻辑分离；历史事实与游戏设定分离；结构化存储

---

## 0. 可行性结论（先看这里）

**总体结论：你指定的方法可以实现。**

可行且建议作为基线的组合：

- Python 3.12+
- FastAPI（编辑器后端）
- Pydantic v2（API Schema / 校验）
- SQLAlchemy 2.0（ORM，方言可切换）
- 分层架构（api / services / domain / repositories / schemas）
- 历史数据与游戏数据分表（或分字段组），禁止互相覆盖
- 项目包（JSON + assets）作为未来游戏客户端的读取契约

技术选型已由你确认，作为后续所有 Phase 的硬约束：

1. 工作库：**MySQL 8**
2. 编辑期 Source of Truth：**MySQL**；JSON 项目包只用于保存/导出/客户端读取
3. 前端：**React + TypeScript + Vite**
4. 编辑器源码版本管理：GitHub 仓库 `https://github.com/fish-dreamsdreams/monkey.git`（公开，用于本仓库源码，不用于用户内容项目）
5. 用户内容项目版本：`schema_version` + 导出快照；编辑器内部不实现 Git

---

## 1. 系统总体架构图

```text
                         ┌──────────────────────────────────────────┐
                         │         三国内容编辑器（本项目）            │
                         │                                          │
  策划/历史顾问 ──UI──►  │  Editor Frontend (React + TS)            │
                         │   人物/关系/技能/城池/势力/地图/事件/剧情 │
                         │   资源管理 / 校验报告 / 导入导出          │
                         └─────────────────┬────────────────────────┘
                                           │ HTTPS + JSON (REST)
                                           │ 后续可选 WebSocket（协作）
                         ┌─────────────────▼────────────────────────┐
                         │  Editor Backend (FastAPI)                │
                         │  api → services → domain → repositories  │
                         │  Pydantic Schema 校验                    │
                         │  领域校验器（时间线/关系/死循环/ID）      │
                         └───────┬───────────────────────┬──────────┘
                                 │                       │
                    ┌────────────▼──────────┐   ┌────────▼────────────┐
                    │  MySQL 8（工作库）     │   │  项目文件系统         │
                    │  结构化主数据          │   │  assets/ 二进制资源   │
                    │  引用完整性 / 查询     │   │  exports/ 导出包      │
                    └────────────┬──────────┘   └────────┬────────────┘
                                 │                       │
                                 └──────────┬────────────┘
                                            │ 导出契约（只读数据包）
                         ┌──────────────────▼───────────────────────┐
                         │  未来游戏客户端（Unity / Unreal / Godot） │
                         │  加载数据 / 战斗 / AI / UI / 动画 / 交互  │
                         │  不写回编辑器业务库                       │
                         └──────────────────────────────────────────┘
```

分层原则：

1. **编辑器负责内容生产**：创建、编辑、校验、保存、查询、资源管理、导出。
2. **游戏客户端负责运行**：加载导出数据，执行战斗、AI、动画、交互。
3. **编辑器禁止写入运行时逻辑**：技能效果只描述数据（效果图/参数），不实现伤害结算循环。
4. **历史层只增改史料，不因平衡性改写。**

---

## 2. 模块划分

```text
┌─ 平台层 ─────────────────────────────────────────────┐
│  ProjectManager     项目创建/打开/保存/导入/导出/版本 │
│  IdentityService    全局 ID 生成与唯一性              │
│  ValidationEngine   跨实体校验（时间线、引用、循环）   │
│  ExportService      面向游戏客户端的数据包导出         │
│  AssetManager       资源入库、预览、绑定、路径校验     │
└──────────────────────────────────────────────────────┘
┌─ 内容域 ─────────────────────────────────────────────┐
│  CharacterModule    人物基础 / 历史 / 游戏属性 / 性格 │
│  RelationshipModule 人物关系（带时间范围）            │
│  SkillModule        技能定义 + 人物技能绑定           │
│  FactionModule      势力（用户可创建，不写死三国）     │
│  CityModule         城池 + 时序归属                   │
│  MapModule          2D 地图、地形、区域、道路河流山脉 │
│  EventModule        历史事件 + 参与者                 │
│  TimelineModule     时间轴与条目                      │
│  StoryModule        Story / Chapter / Node / Choice   │
│  QuestModule        任务（挂接剧情与条件）            │
│  SourceModule       史料来源（正史/演义/设定分离）     │
└──────────────────────────────────────────────────────┘
┌─ 表现与资源 ─────────────────────────────────────────┐
│  ModelAssetModule   模型/贴图/动画元数据              │
│  PreviewModule      头像、图标、地图缩略图预览         │
└──────────────────────────────────────────────────────┘
```

模块依赖方向（只允许实线方向依赖）：

```text
ProjectManager ──► 所有内容域
StoryModule ──► EventModule / CharacterModule / FactionModule / CityModule / QuestModule
QuestModule ──► CharacterModule / CityModule / FactionModule
RelationshipModule ──► CharacterModule
SkillModule ──► CharacterModule（绑定），不依赖战斗引擎
MapModule ──► CityModule
FactionModule ──► CharacterModule / CityModule（引用，不拥有运行逻辑）
AssetManager ──► 被内容域引用（model_id / icon_id）
ValidationEngine ──► 读取所有域，不反向被业务写逻辑依赖
ExportService ──► 读取所有域 + AssetManager
```

---

## 3. 项目目录结构（目标形态）

本仓库是「编辑器产品」；用户创建的每个三国项目是「内容项目包」。

### 3.1 编辑器仓库（本代码库）

```text
sanguo-editor/
├── backend/
│   ├── api/                 # FastAPI 路由，薄层
│   ├── services/            # 用例编排
│   ├── domain/              # 领域对象、领域规则
│   ├── models/              # SQLAlchemy 映射
│   ├── repositories/        # 持久化
│   ├── schemas/             # Pydantic 请求/响应
│   ├── core/                # 配置、日志、异常、ID、时间线工具
│   ├── validation/          # 跨实体校验器
│   └── main.py
├── editor/                  # React + TypeScript 前端
│   ├── components/
│   ├── pages/
│   ├── editors/             # 人物/地图/剧情等专用编辑器
│   └── services/            # 调用后端 API
├── packages/
│   └── game-data-schema/    # 导出数据包 JSON Schema（给未来客户端）
├── data/                    # 开发用示例/种子，不作为运行时主库
├── assets/                  # 编辑器自身资源，不是用户项目资源
├── tests/
├── docs/
│   └── phase0-architecture.md
├── pyproject.toml
└── README.md
```

### 3.2 用户内容项目包（导出/打开的项目）

```text
project/
├── project.json             # 项目元数据、schema_version、校验摘要
├── data/
│   ├── characters/
│   ├── cities/
│   ├── factions/
│   ├── skills/
│   ├── stories/
│   ├── events/
│   ├── quests/
│   ├── maps/
│   └── relationships/
├── assets/
│   ├── characters/
│   ├── models/
│   ├── textures/
│   ├── animations/
│   ├── icons/
│   └── maps/
├── exports/                 # 面向客户端的冻结包
└── editor/                  # 仅编辑器私有状态（布局、草稿），客户端不读
```

**推荐的职责划分：**

| 存储 | 职责 |
| --- | --- |
| MySQL | 编辑期工作库：查询、关联、事务、唯一约束 |
| 项目目录 `assets/` | 二进制资源真实文件 |
| 项目目录 `data/` + `project.json` | 可移植内容快照 / 导入导出 / 客户端读取契约 |
| `exports/` | 校验通过后的只读发布包 |

编辑器打开项目 = 读取项目包 → 导入工作库（或增量同步）。  
保存项目 = 工作库 → 写回项目包。  
导出游戏数据 = 工作库 + 资源 → `exports/` 冻结包。

---

## 4. 核心数据模型（领域，而非实现代码）

所有业务实体使用稳定字符串 ID（推荐 `chr_liu_bei` 这类可读 slug，同时保留内部 UUID 作为主键）。对外 API 用业务 ID。

### 4.1 通用约定

- 时间使用「历史年」为主，月/日可选。未知用 `null`，不用 0。
- 凡会随时间变化的归属，一律使用 `start_year` / `end_year`，禁止只存当前值。
- 每个历史陈述尽量挂 `source_id`。
- `source_type` 枚举：`official_history`（正史）、`historical_book`（史书）、`paper`、`academic`、`tradition`（传统记载）、`folklore`（民间传说）、`literary`（文学演义，含《三国演义》）、`game_setting`（游戏设定）。
- **《三国演义》不得写入 historical_data 的事实字段。** 演义内容进 `literary` 来源，或作为独立 lore 记录。

### 4.2 实体一览

**Project**  
项目元数据：名称、描述、目标年代范围、`schema_version`、内容版本。

**Character**  
基础身份：姓名、字、性别、生卒年、籍贯、民族、身份。  
不直接存「当前势力」作为唯一真相；当前势力由时序成员关系推导，可冗余缓存。

**CharacterHistoricalRecord**（historical_data）  
历史简介、家族背景、人生经历、主要成就、历史评价。只描述史实/史源，不含 HP/攻击力。

**CharacterAttribute**（game_data）  
武力、智力、政治、魅力、统率、体力、士气、移动能力。可按版本/难度存多套，但不覆盖历史表。

**PersonalityTag / CharacterPersonality**  
性格为结构化标签，多对多。预置标签可扩展，不写死为一段文本。

**CharacterRelationship**  
`source_character_id` → `target_character_id`，类型、起止年、描述、史源。关系有向；结义等可成对写入或声明双向规则。

**Source / CharacterHistoricalSource**  
史料实体 + 与人物/事件的引用（书名、类型、引文、页码/卷、备注）。

**Skill**  
技能定义：类型、目标、冷却、消耗、效果参数（JSON 数据，不是 Python 战斗代码）、`historical_basis`。

**CharacterSkill**  
人物与技能绑定，可带来源说明（为何此人有此技能）。

**Faction**  
用户可创建。领袖、颜色、都城、起止年、历史描述。成员与领土均为时序表，不写死曹魏/蜀汉/孙吴。

**FactionMember / FactionTerritory**  
人物入势、城池归属，均带时间范围。

**City**  
名称、历史名称、坐标、人口/军事/经济/防御（游戏层）、建城/毁城年、历史描述。  
`owner` 只作为「某年视图」的派生值。

**Map / TerrainCell / Region / Road / River / Mountain**  
2D 地图。地形网格 + 矢量地物。城池挂在地图坐标上。

**HistoricalEvent**  
年/月/日、地点、描述、后果、史源。参与人物与势力为关联表。

**Timeline / TimelineEntry**  
时间线容器。条目可指向事件、剧情节点、城池易主等。

**Story / StoryChapter / StoryNode / StoryChoice / StoryCondition / StoryAction**  
剧情图。节点类型：dialogue、historical_event、battle、quest、character_join、character_leave、city_capture、faction_create、faction_destroy、choice、condition、reward。  
节点可引用历史事件，但剧情图本身属于游戏叙事层。

**Quest**  
任务目标、前置条件、奖励引用。可挂到剧情节点。

**Resource / ModelAsset**  
资源元数据：类型、路径、checksum、预览。人物通过 `portrait_asset_id` / `model_asset_id` 关联，不把路径散写在人物表各处。

### 4.3 历史数据 vs 游戏数据

```text
                    ┌─────────────────────────────┐
                    │         Character           │
                    │     （稳定身份主键）          │
                    └──────────────┬──────────────┘
           ┌───────────────────────┼───────────────────────┐
           ▼                       ▼                       ▼
 ┌─────────────────┐    ┌────────────────────┐    ┌─────────────────┐
 │ historical_data │    │     game_data      │    │  presentation   │
 │ 生卒、籍贯、事迹 │    │ 属性、技能、数值    │    │ 头像、模型、动画 │
 │ 史源、评价      │    │ 性格战斗倾向        │    │                 │
 └────────┬────────┘    └─────────┬──────────┘    └────────┬────────┘
          │                       │                        │
          │ 禁止用平衡性改写        │ 可迭代调数值             │ 可替换资源
          ▼                       ▼                        ▼
     正史/史书/论文              游戏设定                  AssetManager
     演义单独标记为 literary
```

平衡性调整只允许改 `game_data`。  
若某技能来自演义而非正史，技能的 `historical_basis.source_type = literary`，人物历史简介不得把该技能写成史实。

---

## 5. 数据库 ER 关系

```text
Project 1──* Character
Project 1──* Faction
Project 1──* City
Project 1──* Map
Project 1──* Skill
Project 1──* HistoricalEvent
Project 1──* Story
Project 1──* Quest
Project 1──* Resource
Project 1──* Timeline
Project 1──* Source

Character 1──1 CharacterHistoricalRecord
Character 1──* CharacterAttribute          # 允许多套游戏数值
Character *──* PersonalityTag              # via CharacterPersonality
Character 1──* CharacterRelationship       # 作为 source
Character 1──* CharacterRelationship       # 作为 target
Character *──* Skill                       # via CharacterSkill
Character *──* HistoricalEvent             # via EventParticipant
Character *──* Faction                     # via FactionMember（时序）
Character 0──* ModelAsset / Resource       # 头像、模型

Faction 0──1 Character                     # leader（某时期可另表）
Faction 0──1 City                          # capital（建议时序化）
Faction *──* City                          # via FactionTerritory（时序）

Map 1──* City
Map 1──* TerrainCell
Map 1──* Region
Map 1──* Road
Map 1──* River
Map 1──* Mountain

HistoricalEvent *──* Character
HistoricalEvent *──* Faction
HistoricalEvent 0──1 City                  # location
HistoricalEvent *──* Source

Timeline 1──* TimelineEntry
TimelineEntry 0──1 HistoricalEvent
TimelineEntry 0──1 StoryNode

Story 1──* StoryChapter
StoryChapter 1──* StoryNode
StoryNode 1──* StoryChoice
StoryNode 1──* StoryCondition
StoryNode 1──* StoryAction
StoryNode *──* StoryNode                   # next_nodes 邻接表
StoryNode 0──1 HistoricalEvent
StoryNode *──* Character
Quest 0──1 StoryNode

Resource 1──0..1 ModelAsset（模型类资源的扩展表）
Character / Skill / City / Map  → Resource（外键引用，不存裸路径）
```

关键约束（架构级，后续校验器实现）：

1. `birth_year <= death_year`（若都存在）。
2. 人物作为事件参与者时，事件年必须落在生卒区间内（允许传说例外，但必须标记 `source_type` 且单独开校验开关）。
3. 城池归属区间不可无理由重叠。
4. 剧情 `next_nodes` 必须能从入口到达结束节点，禁止无出口强连通环（允许有条件回边，但要有终止条件）。
5. 全项目业务 ID 唯一。
6. 资源路径必须存在且 checksum 可验证。
7. 关系两端人物必须存在；起止年合法。

---

## 6. 前后端通信方式

**Phase 1–6 采用同步 REST + JSON。**

- 协议：HTTP/1.1，JSON，UTF-8
- 风格：资源型 REST  
  `GET/POST /api/v1/characters`  
  `GET/PUT/DELETE /api/v1/characters/{id}`
- 校验失败：`400` + 结构化错误列表（字段、规则、中文消息）
- 领域冲突：`409`（ID 重复、时间线冲突）
- 统一包裹：`{ "data": ..., "error": ..., "meta": ... }`
- 写操作带 `project_id`（或当前打开项目上下文）
- 后端用 Pydantic 做形状校验，用 ValidationEngine 做跨表语义校验
- 前端不直连数据库

地图编辑器：

- 读取：`GET /maps/{id}` 返回地块与地物
- 保存：按图层 PATCH，避免每次把整个网格当超大 JSON 全量提交（网格大时分块）
- 预览图：静态资源 HTTP，不走 JSON

后续可加、但不进入 MVP：

- WebSocket：多人同时编辑同一人物/地图
- OpenAPI 自动生成前端 client

---

## 7. 编辑器与未来游戏客户端之间的数据流

```text
编辑器工作中
    │  用户改人物属性 / 挂技能 / 排剧情
    ▼
MySQL 工作库 + assets 文件
    │  点击「保存项目」
    ▼
project/data/*.json + project.json
    │  点击「导出游戏数据」（必须先通过 ValidationEngine）
    ▼
project/exports/<version>/
    ├── manifest.json          # schema_version, content_version, checksums
    ├── characters.json
    ├── factions.json
    ├── cities.json
    ├── maps.json
    ├── skills.json
    ├── events.json
    ├── stories.json
    ├── quests.json
    ├── relationships.json
    ├── timeline.json
    └── assets/...             # 仅引用到的资源
    │
    │  游戏客户端只读加载
    ▼
Game Runtime
    加载数据 → 实例化运行对象 → 战斗/AI/UI
    禁止把运行时存档写回编辑器工作库
```

契约原则：

- 客户端依赖 **导出包 schema**，不依赖编辑器数据库。
- 编辑器可以升级内部表结构，只要导出 schema 保持兼容或提供迁移。
- `packages/game-data-schema` 是前后游戏共用的合同，从 Phase 1 就建立版本号，即使早期只有 Character。

---

## 8. 历史数据与游戏数据的关系

| 问题 | 历史层 | 游戏层 |
| --- | --- | --- |
| 刘备是谁 | 姓名/字/生卒/籍贯/身份 | 可用作显示名，但不是战斗数值 |
| 刘备强不强 | 史书评价、事迹 | 武力/智力等可调数值 |
| 八阵图 | 传统记载/文学，标注来源类型 | 减速、加防等效果参数 |
| 桃园结义 | 正史有限度记载 vs 演义情节，必须分源 | 可做成剧情节点/任务 |
| 关羽死亡后 | 历史卒年固定 | 不可再作为存活参战者进入后续事件 |

写入规则：

1. 修改游戏数值 **不得** 改生卒、籍贯、史实描述。
2. 历史记录变更必须选 `source_type`。
3. 校验器区分 `strict_historical` 与 `game_narrative` 两种模式。
4. 默认 UI 分栏：**左侧史实 / 右侧游戏设定**，从人物编辑器第一期就分开。

---

## 9. 地图、人物、剧情、技能、模型之间的关系

```text
Map
 └─ City (坐标)
     ├─ FactionTerritory（某年属于谁）
     └─ HistoricalEvent.location

Character
 ├─ FactionMember（某年属于谁）
 ├─ CharacterRelationship
 ├─ CharacterSkill → Skill（效果数据 + 史源）
 ├─ EventParticipant → HistoricalEvent
 ├─ StoryNode.characters
 └─ portrait/model → Resource/ModelAsset

Story
 └─ StoryNode
     ├─ 可引用 HistoricalEvent（叙事基于时间线）
     ├─ 可触发 Quest
     ├─ 可改变游戏态描述（character_join / city_capture）
     └─ 这些「动作」是数据，不是引擎实现

Skill
 └─ 只描述 effect payload
     例：{ "type": "modify_stat", "stat": "mobility", "target": "enemy", "delta": -20 }
     客户端解释执行；编辑器只校验 schema 与数值范围
```

地图不直接拥有人物。人物通过城池、事件、剧情节点出现在地理与时间中。

---

## 10. 第一阶段 MVP 功能范围

MVP 的目标：**能创建一个内容项目，并用结构化方式管「人」**。证明架构可跑，而不是做完所有编辑器。

### 纳入 MVP（对应你后续 Phase 1 指令）

1. 仓库初始化：Python 3.12、FastAPI、SQLAlchemy 2、Pydantic v2、pytest。
2. MySQL 连接与迁移（Alembic）。
3. 项目最小元数据（至少一个当前项目上下文）。
4. Character CRUD。
5. Character 的 historical_data 与 game_data 分表/分模型。
6. 性格标签结构化（可先预置，允许自定义）。
7. Pydantic schema + 生卒年基础校验。
8. REST API。
9. 最小前端或 API 文档（Swagger）能演示增删改查。
10. 测试：创建、更新、非法生卒年、ID 唯一。

### 明确不纳入 MVP

- 人物关系、技能、城池、势力、地图、事件、剧情、资源管理器
- 完整项目导入导出
- 2D 地图画布
- 游戏客户端
- 运行时战斗逻辑
- 多用户协作
- 《三国演义》全文或自动爬取史料

---

## 11. 后续扩展路线

严格按你规定的顺序，每次只做一个 Phase：

| Phase | 内容 | 退出标准 |
| --- | --- | --- |
| 0 | 架构设计（本文） | 你确认技术选型与存储策略 |
| 1 | 项目初始化 + MySQL + Character | 人物史实/游戏属性可 CRUD，测试通过 |
| 2 | 数据库补全迁移与公共基础设施 | Alembic、统一错误、ID、项目上下文稳定 |
| 3 | 人物管理增强（史料来源、性格完善） | 来源类型可区分演义与正史 |
| 4 | 人物关系 | 有向关系 + 时间范围 + API |
| 5 | 技能系统 | 技能定义与人物绑定，效果仅为数据 |
| 6 | 城池与势力 | 时序归属，势力可用户创建 |
| 7 | 2D 地图编辑器 | 地形/城池/道路/河流/山脉 |
| 8 | 历史事件 | 参与者校验生卒 |
| 9 | 剧情编辑器 | 节点图 + 环检测 |
| 10 | 资源/模型管理 | 路径存在性、人物绑定模型 |
| 11 | 跨实体数据校验引擎 | 时间线、易主、死循环 |
| 12 | 项目导入导出 | 生成客户端可读包 |
| 13 | 游戏客户端数据接口冻结 | schema 版本与示例加载器 |

---

## 推荐技术选型（Phase 0 建议，待你确认）

| 项 | 推荐 | 原因 |
| --- | --- | --- |
| 后端 | FastAPI + Python 3.12 | 与需求一致，类型友好 |
| Schema | Pydantic v2 | API 与导出校验 |
| ORM | SQLAlchemy 2.0 + Alembic | 可切换 MySQL/SQLite |
| 工作库 | MySQL 8 | 符合你后补的 Phase 1 指令，约束与并发更好 |
| 项目包 | JSON 文件 + assets | 满足目录结构，客户端不依赖 MySQL |
| 前端 | React + TypeScript + Vite | 地图编辑器需要 Canvas/SVG；比桌面 GUI 更利于后续扩展 |
| 地图 | 先 SVG/Canvas 2D | 满足第一阶段，不为 Unity 提前耦合 |
| 测试 | pytest + httpx | API 级测试 |

不推荐把编辑器做成纯 SQLite 文件数据库作为唯一存储——与「项目目录结构化 JSON」和「未来客户端读取」都不如「MySQL 工作库 + JSON 导出」清晰。  
SQLite 可保留为后期「单文件便携项目」选项，不作为 Phase 1 主路径。

---

## 已确认决策

| 项 | 结论 |
| --- | --- |
| 工作库 | MySQL 8。SQLAlchemy 2.0，不把 SQL 写死为 MySQL 专有语法，便于以后加 SQLite 便携模式 |
| Source of Truth | 编辑期以 MySQL 为准；保存项目/导出游戏数据时生成 JSON 项目包；客户端只读导出包 |
| 前端 | React + TypeScript + Vite；地图编辑器后续用 Canvas/SVG；Phase 1 可以先 API + Swagger，但仓库预留 `editor/` |
| 内容版本 | `project.json` 记录 `schema_version` 与 `content_version`；导出包可冻结快照 |
| 编辑器源码版本 | GitHub 公开仓库 `https://github.com/fish-dreamsdreams/monkey.git`，仅管理编辑器源码 |
| 内容项目版本 | `schema_version` + 导出快照；与源码 Git 分离 |

## Git 接通状态

已确认并完成本地接通（**未 push**）：

- 远程：公开空仓库，`default_branch = main`，当前无业务代码
- 本地：`E:\三国2` 执行 `git init -b main`
- remote：`origin` → `https://github.com/fish-dreamsdreams/monkey.git`
- 用途：编辑器源码版本管理
- 非用途：用户三国内容项目不走这个 Git 流程

首次向 GitHub 发布需要你明确说「提交并 push」之后才会执行。

---

## Phase 1 将做什么（仅在你确认后）

只做：

- 仓库与目录骨架
- MySQL + SQLAlchemy + Pydantic
- Character 人物管理（基础信息 + 历史信息 + 游戏属性 + 性格标签）
- 对应测试与运行方式

不做：关系、技能、城池、地图、事件、剧情、资源、导入导出。
