# COC 跑团游戏系统

基于 LangChain + DeepSeek + FastAPI 的克苏鲁神话(Call of Cthulhu)跑团游戏系统，支持 AI 游戏主持人(GM)、骰子系统、场景管理等功能。

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

---

## 项目架构

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
              ┌───────────────────────────┐
              │     后端统一服务           │
              │      (FastAPI)            │
              │     端口: 5780            │
              │                           │
              │  ┌─────────────────────┐  │
              │  │   player_router     │  │
              │  │   /api/* 玩家数据   │  │
              │  └─────────────────────┘  │
              │  ┌─────────────────────┐  │
              │  │   chat_router       │  │
              │  │   /chat/* AI对话    │  │
              │  └─────────────────────┘  │
              └─────────────┬─────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                                       ▼
┌───────────────┐              ┌───────────────────────────┐
│    MySQL      │              │      LangChain Agent      │
│   数据库      │              │  ┌─────────────────────┐  │
│               │              │  │   DeepSeek LLM      │  │
│ - players    │              │  │   场景管理器         │  │
│ - skills     │              │  │   骰子服务          │  │
│ - chinese_name│              │  │   MCP工具集         │  │
└───────────────┘              │  └─────────────────────┘  │
                               └───────────────────────────┘
```

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
├── .env                      # 环境变量配置(需自行创建)
├── test_log.py               # 日志测试脚本
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
├── scenes/                   # 剧本场景文件夹
│   ├── 开始-连接-结尾.txt    # 主线剧本
│   └── scene（xxx）.txt      # 场景剧本
│
└── src_test/                 # 源代码目录(重构后)
    ├── adapter/              # 适配器层(API服务)
    │   ├── api/              # FastAPI路由
    │   │   ├── main.py       # API主入口
    │   │   ├── chat_router.py    # 对话服务
    │   │   ├── player_router.py  # 玩家数据
    │   │   └── auth_router.py    # 认证服务
    │   └── cli/              # 命令行入口
    │       └── chat.py       # CLI对话
    │
    ├── service/              # 服务层
    │   ├── agent_service.py  # Agent服务
    │   ├── scene_service.py  # 场景管理
    │   └── dice_service.py   # 骰子服务
    │
    ├── domain/               # 领域层
    │   ├── models/           # 数据模型
    │   │   ├── player.py     # 玩家模型
    │   │   ├── skill.py      # 技能模型
    │   │   └── scene.py      # 场景模型
    │   └── dice/             # 骰子领域逻辑
    │       ├── roll.py       # 投掷逻辑
    │       └── expr.py       # 表达式解析
    │
    └── infrastructure/       # 基础设施层
        ├── database/         # 数据库
        │   ├── connection.py # 连接管理
        │   └── repository.py # 数据仓库
        ├── file/             # 文件操作
        │   └── txt_loader.py # 剧本加载
        └── log/              # 日志模块
            └── logger.py     # 日志配置
```

---

## 服务端口

| 端口 | 服务 | 说明 |
|------|------|------|
| 5770 | 前端HTTP服务 | 静态文件服务，游戏页面入口 |
| 5780 | 后端统一服务 | 玩家数据、AI对话、场景管理 |

---

## 快速开始

### 1. 环境准备

```bash
# 创建conda环境
conda create -n python20251006 python=3.10
conda activate python20251006

# 安装依赖(使用清华源)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_URL=https://api.deepseek.com
```

### 3. 测试日志功能

```bash
python test_log.py
```

检查 `logs/` 目录下生成的日志文件。

### 4. 启动服务

```bash
cd src_test/front
start.bat
```

### 5. 访问游戏

浏览器打开: `http://localhost:5770/game.html`

---

## API 接口文档

> API文档地址: http://localhost:5780/docs

### 1. 玩家数据接口 (/api)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/player/{player_id}` | 获取玩家信息 |
| GET | `/api/skills/{player_id}` | 获取玩家技能 |
| GET | `/api/health` | 健康检查 |

### 2. 对话服务接口 (/chat)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/chat/init` | 初始化Agent |
| POST | `/chat/send` | 发送消息(流式) |
| POST | `/chat/reset-all` | 重置所有记忆 |
| GET | `/chat/scene` | 获取场景信息 |
| GET | `/chat/logs` | 获取日志 |
| GET | `/chat/health` | 健康检查 |

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

**健康检测**: 每30秒自动检测后端服务状态

### chat.js - 对话模块

- `ChatModule.checkStatus()` - 检查服务状态
- `ChatModule.initAgent()` - 初始化Agent
- `ChatModule.sendMessage()` - 发送消息(流式)
- `ChatModule.resetAllMemory()` - 重置记忆

---

## 核心模块

### ThreadManager - 场景管理器

支持嵌套场景，每个场景有独立的记忆线程。

```python
manager.enter_scene("墓地")  # 进入场景
manager.exit_scene()         # 退出场景
manager.get_scene_path()     # 获取场景路径
```

### MCP工具集

| 工具 | 功能 |
|------|------|
| `roll_dice_tool` | 骰子投掷 (如 2d6+5) |
| `roll_attribute_check_tool` | 属性/技能检定 |
| `roll_sanity_check_tool` | 理智检定 |
| `new_scene` | 进入新场景 |
| `exit_scene` | 退出场景 |

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
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
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

## 开发指南

### 添加新的日志记录

```python
from src_test.infrastructure.log import get_logger

logger = get_logger("YOUR_CONTEXT")
logger.info("操作信息")
logger.error("错误信息", exc_info=True)
```

### 添加新的MCP工具

1. 在 `service/agent_service.py` 中定义工具函数
2. 添加到 `tools` 列表
3. 使用logger记录调用和结果

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
