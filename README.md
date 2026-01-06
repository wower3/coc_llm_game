# COC 跑团游戏系统

基于 LangChain + DeepSeek + FastAPI 的克苏鲁神话(Call of Cthulhu)跑团游戏系统，支持 AI 游戏主持人(GM)、骰子系统、场景管理等功能。

采用**领域驱动设计(DDD)**架构，严格分层：**Adapter → Service → Domain → Infrastructure**

## 目录

- [项目架构](#项目架构)
- [技术栈](#技术栈)
- [目录结构](#目录结构)
- [快速开始](#快速开始)
- [服务端口](#服务端口)
- [API 接口文档](#api-接口文档)
- [前端组件](#前端组件)
- [核心模块](#核心模块)
- [日志系统](#日志系统)
- [配置说明](#配置说明)
- [开发指南](#开发指南)
- [架构设计原则](#架构设计原则)

---

## 项目架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (Vue.js)                            │
│                    http://localhost:5770                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  game.html  │  │  game.js    │  │       chat.js           │  │
│  │  游戏界面    │  │  主逻辑     │  │   对话模块(API调用)      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP请求
                            ▼
              ┌─────────────────────────────────────┐
              │        适配器层 (Adapter)           │
              │           FastAPI                   │
              │          端口: 5780                 │
              │                                     │
              │  ┌───────────────────────────────┐  │
              │  │     main.py (应用入口)        │  │
              │  └───────┬───────────┬───────────┘  │
              │          │           │              │
│  ┌───────────▼──┐  ┌───▼────┐  ┌──▼───────────┐  │
│  │player_router │  │chat_   │  │  auth_router │  │
│  │/api/* 玩家   │  │router  │  │  /auth/* 认证 │  │
│  └──────────────┘  │/chat/* │  └──────────────┘  │
│                    └────────┘                    │
              └─────────────────┬───────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│PlayerService │      │AgentService  │      │SceneService  │
│ 玩家服务     │      │ Agent服务    │      │ 场景管理     │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                      │                      │
       └──────────────────────┴──────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
  ┌──────────────────────┐        ┌──────────────────────┐
  │   Repository         │        │    Domain            │
  │   数据仓储           │        │    领域模型          │
  │                      │        │  - PlayerModel       │
  │  - PlayerRepository  │        │  - SkillsModel       │
  │  - CRUD操作          │        │  - Dice逻辑          │
  └──────────┬───────────┘        └──────────────────────┘
             │
             ▼
  ┌──────────────────────────────────────────────────────┐
  │        Infrastructure - Database Connection         │
  │  ┌──────────────────────────────────────────────┐  │
  │  │   connection.py (MySQL连接池管理)            │  │
  │  │   - execute_query(sql, params)               │  │
  │  │   - execute_update(sql, params)              │  │
  │  └──────────────────┬───────────────────────────┘  │
  └─────────────────────┼──────────────────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │    MySQL 数据库  │
              │  - players      │
              │  - skills       │
              │  - chinese_name│
              └─────────────────┘
```

### 分层说明

| 层级 | 路径 | 职责 |
|------|------|------|
| **Adapter** | `adapter/` | 处理HTTP请求，参数验证，调用Service |
| **Service** | `service/` | 业务逻辑协调，编排Domain和Infrastructure |
| **Domain** | `domain/` | 核心业务模型和规则，不依赖外部 |
| **Infrastructure** | `infrastructure/` | 数据库、文件、日志等基础服务 |

**重要原则**：
- ❌ 禁止跨层调用（如 Service → Database）
- ✅ 调用链：Adapter → Service → Repository → Database
- ✅ 所有SQL使用参数化查询，防止注入

---

## 技术栈

### 后端
| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 运行环境 |
| FastAPI | 0.125.0 | Web框架 |
| Uvicorn | 0.38.0 | ASGI服务器 |
| LangChain | 1.1.0 | AI Agent框架 |
| LangGraph | 1.0.4 | 状态管理 |
| DeepSeek | - | LLM模型 |
| PyMySQL | 1.1.2 | 数据库连接 |
| Pydantic | 2.12.5 | 数据验证 |
| Loguru | 0.7.2 | 日志管理 |

### 前端
| 技术 | 版本 | 用途 |
|------|------|------|
| Vue.js | 3.x (CDN) | 前端框架 |
| HTML5/CSS3 | - | 页面结构和样式 |
| JavaScript | ES6+ | 交互逻辑 |

---

## 目录结构

```
coc_structure/
├── README.md                 # 项目文档
├── README_AI.md              # AI对话用精简文档
├── requirements.txt          # Python依赖
├── setup_venv.bat            # 虚拟环境安装脚本(Windows)
├── start.bat                 # 一键启动脚本(Windows)
├── .gitignore                # Git忽略文件配置
├── .env                      # 环境变量配置(需自行创建)
├── test_log.py               # 日志测试脚本
│
├── character/                # 角色数据目录
│   ├── keeper/              # 守密人相关
│   ├── npc/                 # NPC角色数据
│   └── player/              # 玩家角色数据
│       └── 0000001.json     # 示例玩家角色卡
│
├── scenes/                   # 剧本场景文件夹
│   ├── scenes.txt           # 场景配置文件
│   ├── 开始-连接-结尾.txt    # 主线剧本
│   └── scene（xxx）.txt      # 场景剧本文件
│
├── logs/                     # 日志目录(自动生成)
│   ├── {YYYYMMDD_HHMMSS}_pid{PID}/              # 每次运行的独立文件夹
│   │   ├── all.log         # 所有日志
│   │   ├── api.log         # API请求日志
│   │   ├── agent.log       # Agent交互日志
│   │   ├── scene.log       # 场景切换日志
│   │   ├── dice.log        # 骰子投掷日志
│   │   └── error.log       # 错误日志
│   ├── history/            # 归档的历史日志
│   │   └── {YYYYMMDD}/     # 按日期分类的归档
│   ├── 归档旧日志.bat      # 日志归档脚本
│   └── archive_logs.ps1    # 归档脚本(PowerShell)
│
└── src_test/                 # 源代码目录(DDD架构重构后)
    │
    ├── adapter/              # 适配器层 (Adapter Layer)
    │   ├── api/              # FastAPI路由
    │   │   ├── main.py       # API主入口，集成所有路由
    │   │   ├── chat_router.py    # 对话服务路由
    │   │   ├── player_router.py  # 玩家数据路由
    │   │   └── auth_router.py    # 认证服务路由
    │   └── cli/              # 命令行入口
    │       └── chat.py       # CLI对话入口
    │
    ├── service/              # 服务层 (Service Layer)
    │   ├── agent_service.py  # AI Agent服务
    │   ├── scene_service.py  # 场景管理服务
    │   ├── dice_service.py   # 骰子服务
    │   ├── player_service.py # 玩家数据服务
    │   └── single_agent_service.py # 单Agent服务
    │
    ├── domain/               # 领域层 (Domain Layer)
    │   ├── models/           # 数据模型
    │   │   ├── player.py     # COC 7版玩家角色模型
    │   │   ├── skill.py      # 技能模型
    │   │   └── scene.py      # 场景信息模型
    │   └── dice/             # 骰子领域逻辑
    │       ├── roll.py       # 投掷核心逻辑
    │       └── expr.py       # 表达式词法分析
    │
    ├── front/                # 前端文件
    │   ├── game.html         # 游戏主页面
    │   ├── game.js           # 游戏主逻辑
    │   ├── chat.js           # 对话模块
    │   └── vue/              # Vue.js相关文件
    │       ├── index.html
    │       └── main.js
    │
    └── infrastructure/       # 基础设施层 (Infrastructure Layer)
        ├── database/         # 数据库
        │   ├── connection.py # MySQL连接池管理
        │   └── repository.py # 数据仓储实现(CRUD)
        ├── file/             # 文件操作
        │   └── txt_loader.py # 剧本文件加载器
        └── log/              # 日志系统
            └── logger.py     # 基于loguru的分布式日志
```

### 架构层次详解

#### Adapter 层 (适配器层)
- **职责**: 处理外部请求，参数验证，调用 Service 层
- **文件**: `adapter/api/*.py`
- **特点**: 不包含业务逻辑，只做请求/响应转换

#### Service 层 (服务层)
- **职责**: 编排业务逻辑，协调 Domain 和 Infrastructure
- **文件**: `service/*.py`
- **特点**: 实现用例，处理事务边界

#### Domain 层 (领域层)
- **职责**: 核心业务模型和规则
- **文件**: `domain/models/*.py`, `domain/dice/*.py`
- **特点**: 不依赖任何外部框架，纯净的业务逻辑

#### Infrastructure 层 (基础设施层)
- **职责**: 提供技术能力（数据库、文件、日志等）
- **文件**: `infrastructure/**/*.py`
- **特点**: 被 Service 层调用，不调用上层

---

## 服务端口

| 端口 | 服务 | 说明 |
|------|------|------|
| 5770 | 前端HTTP服务 | 静态文件服务，游戏页面入口 |
| 5780 | 后端统一服务 | 玩家数据、AI对话、场景管理 |

---

## 快速开始

### 一键启动（推荐）

项目已配置为独立的虚拟环境，无需手动安装依赖：

#### Windows 用户

```bash
# 1. 首次运行：安装虚拟环境
setup_venv.bat

# 2. 启动游戏
start.bat
```

#### Linux/Mac 用户

```bash
# 1. 首次运行：安装虚拟环境
chmod +x setup_venv.sh start.sh
./setup_venv.sh

# 2. 启动游戏
./start.sh
```

### 手动安装（可选）

如果需要手动安装：

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖(使用清华源)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 配置环境变量

在项目根目录创建 `.env` 文件：

```env
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_URL=https://api.deepseek.com
```

### 访问游戏

浏览器打开: `http://localhost:5770/game.html`

### 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:5770 | 游戏页面 |
| 后端 | http://localhost:5780 | API 服务 |
| API 文档 | http://localhost:5780/docs | Swagger 文档 |

---

## API 接口文档

> 交互式 API 文档: http://localhost:5780/docs

### 1. 玩家数据接口 (/api)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/player/{player_id}` | 获取玩家完整信息（含计算属性） |
| GET | `/api/skills/{player_id}` | 获取玩家技能列表（可过滤） |
| GET | `/api/skills/{player_id}/{skill_id}` | 获取单个技能值 |
| GET | `/api/skill/name/{skill_id}` | 获取技能中文名 |
| POST | `/api/skill/query` | 通过技能名/ID查询技能值 |
| POST | `/api/player/update` | 更新玩家数据 |
| GET | `/api/equipments/{player_id}` | 获取玩家装备列表 |
| GET | `/api/health` | 健康检查 |

**请求示例**:
```bash
# 获取玩家信息
curl http://localhost:5780/api/player/0000001

# 查询技能值（支持中文名和ID）
curl -X POST http://localhost:5780/api/skill/query \
  -H "Content-Type: application/json" \
  -d '{"player_id": "0000001", "query": "魅惑"}'
```

### 2. 对话服务接口 (/chat)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/chat/init` | 初始化Agent（指定场景和玩家） |
| POST | `/chat/send` | 发送消息（流式响应） |
| POST | `/chat/reset-all` | 重置所有记忆 |
| GET | `/chat/scene` | 获取当前场景信息 |
| GET | `/chat/logs` | 获取运行日志 |
| GET | `/chat/log-file` | 获取实时日志文件内容 |
| GET | `/chat/health` | 健康检查 |

**请求示例**:
```bash
# 初始化对话
curl -X POST http://localhost:5780/chat/init \
  -H "Content-Type: application/json" \
  -d '{"scene": "开始", "player_id": "0000001"}'

# 发送消息
curl -X POST http://localhost:5780/chat/send \
  -H "Content-Type: application/json" \
  -d '{"message": "我要检查墓地", "user_id": "user123"}'
```

---

## 前端组件

### game.html - 游戏主页面

- **左侧面板**: 调查员信息、属性、技能
- **中间面板**: 对话区域、消息输入
- **右侧面板**: 物品栏、可选行动

### game.js - 主逻辑

- `checkChatStatus()` - 检查服务状态并自动初始化（每30秒）
- `sendMessage()` - 发送消息
- `resetAllMemory()` - 重置记忆
- `showLogs()` - 显示实时日志窗口
- `refreshLogFile()` - 刷新日志文件内容
- `toggleAutoRefresh()` - 切换日志自动刷新（每3秒）

**健康检测**: 每30秒自动检测后端服务状态
**日志查看**: 点击顶部菜单"系统日志"查看实时日志，支持自动刷新

### chat.js - 对话模块

- `ChatModule.checkStatus()` - 检查服务状态
- `ChatModule.initAgent()` - 初始化Agent
- `ChatModule.sendMessage()` - 发送消息(流式)
- `ChatModule.resetAllMemory()` - 重置记忆

---

## 核心模块

### Service 层 (服务层)

#### PlayerService - 玩家数据服务
**文件**: `src_test/service/player_service.py`

| 方法 | 功能 |
|------|------|
| `get_player_info()` | 获取玩家完整信息（含衍生属性） |
| `get_filtered_skills()` | 获取技能列表（支持过滤） |
| `get_skill_value_by_name_or_id()` | 通过技能名/ID查询技能值 |
| `get_skill_chinese_name()` | 获取技能中文名 |
| `get_player_equipments()` | 获取玩家装备列表 |

#### AgentService - AI Agent 服务
**文件**: `src_test/service/agent_service.py`

| 方法 | 功能 |
|------|------|
| `initialize_agent()` | 初始化AI Agent |
| `chat()` | 发送消息并获取流式响应 |
| `reset_all_memory()` | 重置所有记忆 |
| `get_current_scene()` | 获取当前场景信息 |

#### SceneService - 场景管理服务
**文件**: `src_test/service/scene_service.py`

| 方法 | 功能 |
|------|------|
| `load_scene()` | 加载场景剧本 |
| `get_scene_info()` | 获取场景信息 |
| `enter_scene()` | 进入新场景 |
| `exit_scene()` | 退出场景 |

#### DiceService - 骰子服务
**文件**: `src_test/service/dice_service.py`

| 方法 | 功能 |
|------|------|
| `roll_dice()` | 投掷骰子（支持表达式） |
| `roll_attribute_check()` | 属性/技能检定 |
| `roll_sanity_check()` | 理智检定 |

### Repository 层 (数据仓储)

**文件**: `src_test/infrastructure/database/repository.py`

| 方法 | 功能 | SQL安全 |
|------|------|---------|
| `get_user_card()` | 获取玩家卡片 | ✅ 参数化 |
| `set_user_card()` | 更新玩家数据 | ✅ 参数化+白名单 |
| `get_skill_card()` | 获取技能卡片 | ✅ 参数化 |
| `get_single_skill_value()` | 获取单个技能值 | ✅ 参数化+列名验证 |
| `get_id()` | 中文名转ID | ✅ 参数化 |
| `get_name_by_id()` | ID转中文名 | ✅ 参数化 |
| `get_all_chinese_names()` | 获取所有中文名映射 | ✅ 参数化 |
| `get_skill_id_by_name()` | 通过中文名获取ID | ✅ 参数化 |

**安全特性**：
- 所有SQL查询使用参数化查询
- 动态列名使用正则验证（只允许ASCII字母、数字、下划线）
- 列名白名单验证（防止SQL注入）
- 字符串值使用参数化传递

### Domain 层 (领域模型)

#### COCPlayerModel - 玩家角色模型
**文件**: `src_test/domain/models/player.py`

完整的 COC 7版 角色数据模型，包含：
- 基本属性：力量、体质、体型、敏捷、外貌、智力、意志、幸运
- 衍生属性：生命值、魔法值、理智值、伤害加值、体格、移动力
- 技能系统：80+ 技能字段
- 装备系统：武器、装备、背包装备
- 战斗数据：伤害、体格、移动力

#### SkillsModel - 技能模型
**文件**: `src_test/domain/models/skill.py`

所有技能的完整数据结构。

#### SceneInfo - 场景信息模型
**文件**: `src_test/domain/models/scene.py`

场景名称、描述和关联信息。

### Dice 领域逻辑

#### roll.py - 骰子投掷
**文件**: `src_test/domain/dice/roll.py`

实现 COC 规则的骰子投掷逻辑：
- 基础投掷：d4, d6, d8, d10, d20, d100
- 复杂表达式：2d6+5, 1d100+30
- 暗骰功能

#### expr.py - 表达式解析
**文件**: `src_test/domain/dice/expr.py`

骰子表达式的词法分析和解析。

### ThreadManager - 场景线程管理器

支持嵌套场景，每个场景有独立的记忆线程。

```python
# 进入场景
manager.enter_scene("墓地")

# 退出场景
manager.exit_scene()

# 获取场景路径
manager.get_scene_path()  # ["开始", "墓地"]
```

### MCP 工具集

| 工具 | 功能 | 实现位置 |
|------|------|---------|
| `roll_dice_tool` | 骰子投掷 (如 2d6+5) | agent_service.py |
| `roll_attribute_check_tool` | 属性/技能检定 | agent_service.py |
| `roll_sanity_check_tool` | 理智检定 | agent_service.py |
| `new_scene` | 进入新场景 | agent_service.py |
| `exit_scene` | 退出场景 | agent_service.py |

---

## 日志系统

项目使用 **loguru** 实现全面的日志记录，所有调用、传输消息、报错信息都会被记录到 `logs/` 目录。

### 日志文件结构

每次运行会创建独立的日志文件夹：`logs/{YYYYMMDD_HHMMSS}_pid{PID}/`

| 文件 | 内容 | 级别 |
|------|------|------|
| `all.log` | 所有日志 | DEBUG |
| `api.log` | API请求/响应 | INFO |
| `agent.log` | Agent交互 | DEBUG |
| `scene.log` | 场景切换 | INFO |
| `dice.log` | 骰子投掷 | INFO |
| `error.log` | 错误信息 | ERROR |

**文件夹命名格式**: `{日期时分秒}_进程ID`
- 每次运行生成独立文件夹，不会覆盖
- 示例: `20260104_105942_pid40972/`

### 日志归档

使用 `logs/归档旧日志.bat` 脚本可以：
- 将昨天及之前的日志文件夹压缩
- 按日期分类存放到 `logs/history/{YYYYMMDD}/` 目录
- 自动删除已归档的源文件夹

### 日志特性

- **独立文件夹**: 每次运行独立目录，互不干扰
- **自动轮转**: 每天午夜自动创建新日志文件
- **压缩存储**: 旧日志自动压缩为zip格式
- **自动清理**: 30天后自动删除过期日志
- **上下文过滤**: 根据上下文(API/AGENT/SCENE/DICE)自动分发到对应文件

### 使用示例

```python
from src_test.infrastructure.log import get_logger

# 获取通用logger
logger = get_logger()

# 获取带上下文的logger
api_logger = get_logger("API")
agent_logger = get_logger("AGENT")

# 记录日志
logger.info("普通信息日志")
logger.error("错误日志", exc_info=True)
```

---

## 配置说明

### 环境变量 (.env)

```env
# DeepSeek API配置
DEEPSEEK_API_KEY=sk-xxxxxx
DEEPSEEK_URL=https://api.deepseek.com

# 数据库配置(可选)
HOST=localhost
PORT=3306
USER=root
MYSQL_PW=your_password
DB_NAME=coc_game
```

### 场景配置 (scenes/scenes.txt)

```
场景名称:最大进入次数
墓地:3
图书馆:2
密室:1
```

### Git忽略配置 (.gitignore)

项目已配置忽略以下内容：

| 规则 | 说明 |
|------|------|
| `logs/` | 所有日志目录和文件 |
| `*.log` | 所有.log文件 |
| `.env` | 环境变量配置（包含敏感信息） |
| `.claude/` | Claude Code配置 |
| `__pycache__/` | Python缓存 |
| `*.pyc` | Python编译文件 |
| `.venv/` | 虚拟环境目录 |

---

## 架构设计原则

### 1. 分层架构原则

项目严格遵循 DDD (领域驱动设计) 的分层架构：

```
Adapter → Service → Repository → Database
```

**调用规则**：
- ✅ 上层可以调用下层
- ❌ 下层不能调用上层
- ❌ 禁止跨层调用（如 Service 直接调用 Database）

**正确示例**：
```python
# Service 层调用 Repository 层 ✅
class PlayerService:
    def __init__(self):
        self.repository = get_repository()

    def get_player_info(self, player_id: str):
        return self.repository.get_user_card(player_id)
```

**错误示例**：
```python
# Service 层直接调用 Database ❌ 越级调用
class PlayerService:
    def get_skill_id_by_name(self, skill_name: str):
        # 错误：绕过了 Repository 层
        results = self.repository.db.execute_query(sql, (skill_name,))
        return results
```

### 2. SQL 安全原则

所有数据库操作必须使用**参数化查询**，防止 SQL 注入：

```python
# ✅ 正确：使用参数化查询
sql = "SELECT * FROM players WHERE id = %s"
results = self.db.execute_query(sql, (user_id,))

# ❌ 错误：使用 f-string 拼接
sql = f"SELECT * FROM players WHERE id = '{user_id}'"  # SQL注入风险
```

**列名拼接的特殊处理**：

当需要动态拼接列名时（无法参数化），必须使用**正则验证**：

```python
# 验证列名只包含ASCII字母、数字、下划线
if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', skill_id):
    return None

sql = f"SELECT `{skill_id}` FROM skills WHERE id = %s"
results = self.db.execute_query(sql, (user_id,))
```

**列名白名单验证**（用于动态更新）：

```python
allowed_columns = {'name', 'age', 'strength', 'constitution', ...}
if key not in allowed_columns:
    logger.warning(f"忽略非法列名: {key}")
    continue
```

### 3. 依赖倒置原则

- Domain 层不依赖任何外部框架
- Service 层依赖 Domain 层的接口/模型
- Infrastructure 层被 Service 层调用，不反向依赖

### 4. 单一职责原则

每个模块只负责一个功能：
- **Adapter**: 处理 HTTP 请求/响应
- **Service**: 编排业务逻辑
- **Repository**: 数据访问
- **Model**: 数据结构定义

### 5. 开放封闭原则

- 对扩展开放：添加新功能通过新增 Service/Router
- 对修改封闭：不修改已有代码

---

## 开发指南

### 添加新的日志记录

```python
from src_test.infrastructure.log import get_logger

logger = get_logger("YOUR_CONTEXT")
logger.info("操作信息")
logger.error("错误信息", exc_info=True)
```

### 添加新的 API 接口

1. **在 Adapter 层创建路由** (`adapter/api/your_router.py`):

```python
from fastapi import APIRouter, Depends
from typing import Optional

router = APIRouter(prefix="/your-module", tags=["Your Module"])

@router.get("/items/{item_id}")
async def get_item(item_id: str):
    # 调用 Service 层
    pass
```

2. **在 Service 层实现业务逻辑** (`service/your_service.py`):

```python
from src_test.infrastructure.database import get_repository
from src_test.infrastructure.log import get_logger

logger = get_logger("YOUR_SERVICE")

class YourService:
    def __init__(self):
        self.repository = get_repository()

    def get_item(self, item_id: str):
        logger.debug(f"查询项目: {item_id}")
        return self.repository.get_item(item_id)
```

3. **在 main.py 中注册路由**:

```python
from src_test.adapter.api import your_router

app.include_router(your_router.router)
```

### 添加新的数据模型

**在 Domain 层定义模型** (`domain/models/your_model.py`):

```python
from pydantic import BaseModel

class YourModel(BaseModel):
    id: str
    name: str
    value: int

    class Config:
        from_attributes = True
```

### 添加新的数据库操作

**在 Repository 层实现** (`infrastructure/database/repository.py`):

```python
def get_your_data(self, item_id: str) -> Optional[Dict[str, Any]]:
    """获取数据"""
    logger.debug(f"[数据库] 查询数据: item_id={item_id}")
    try:
        sql = "SELECT * FROM your_table WHERE id = %s"
        results = self.db.execute_query(sql, (item_id,))

        if results:
            return results[0]
        return None
    except Exception as e:
        logger.error(f"[数据库] 查询失败: {str(e)}", exc_info=True)
        return None
```

**重要**：
- ✅ 使用参数化查询
- ✅ 添加异常处理
- ✅ 记录详细日志

### 添加新的 MCP 工具

1. **在 agent_service.py 中定义工具函数**:

```python
def your_new_tool(input_str: str) -> str:
    """
    工具描述

    Args:
        input_str: 输入参数

    Returns:
        str: 返回结果
    """
    logger.info(f"[MCP工具] your_new_tool 调用: input={input_str}")
    try:
        # 实现工具逻辑
        result = do_something(input_str)
        logger.info(f"[MCP工具] your_new_tool 完成: result={result}")
        return result
    except Exception as e:
        logger.error(f"[MCP工具] your_new_tool 失败: {str(e)}", exc_info=True)
        return f"工具执行失败: {str(e)}"
```

2. **添加到工具列表**:

```python
tools = [
    roll_dice_tool,
    roll_attribute_check_tool,
    your_new_tool,  # 添加新工具
]
```

### 代码审查清单

提交代码前，请检查：

- [ ] 是否遵循分层架构（Adapter → Service → Repository）
- [ ] SQL 查询是否使用参数化
- [ ] 是否添加了适当的日志记录
- [ ] 是否添加了异常处理
- [ ] 是否添加了类型注解
- [ ] 是否添加了文档字符串

### 运行测试

```bash
# 测试日志功能
python test_log.py

# 测试CLI对话
python -m src_test.adapter.cli.chat
```

---

## License

MIT License
