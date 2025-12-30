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
│
├── scenes/                   # 剧本场景文件夹
│   ├── 开始-连接-结尾.txt    # 主线剧本
│   └── scene（xxx）.txt      # 场景剧本
│
└── src/                      # 源代码目录
    ├── adapter/              # 适配器层(API服务)
    │   ├── backend_api.py    # 后端主入口 (端口5780)
    │   ├── player_router.py  # 玩家数据路由 /api/*
    │   └── chat_router.py    # 对话服务路由 /chat/*
    │
    ├── agent/                # AI Agent核心
    │   ├── test_agent.py     # Agent主入口
    │   ├── chat.py           # 命令行对话
    │   ├── agentService/     # Agent服务
    │   │   └── service_mcp.py  # MCP服务和场景管理
    │   └── dice/             # 骰子模块
    │       ├── dice_mcp.py   # 骰子MCP服务
    │       ├── roll.py       # 骰子投掷逻辑
    │       └── model.py      # 数据模型
    │
    ├── front/                # 前端文件
    │   ├── start.bat         # 一键启动脚本
    │   ├── game.html         # 游戏主页面
    │   ├── game.js           # 游戏主逻辑
    │   └── chat.js           # 对话模块
    │
    └── util/                 # 工具类
        └── load_txt_with_keyword.py  # 剧本文件加载
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

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_URL=https://api.deepseek.com
```

### 3. 启动服务

```bash
cd src/front
start.bat
```

### 4. 访问游戏

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

- `checkChatStatus()` - 检查服务状态并自动初始化
- `sendMessage()` - 发送消息
- `resetAllMemory()` - 重置记忆

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

## License

MIT License
