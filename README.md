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
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   API服务      │  │ 对话管理服务   │  │  AI对话服务    │
│   (FastAPI)   │  │  (FastAPI)    │  │  (FastAPI)    │
│  端口: 5780   │  │  端口: 5781   │  │  端口: 5782   │
│               │  │               │  │               │
│ - 玩家数据    │  │ - 启动/停止   │  │ - AI对话      │
│ - 技能查询    │  │   对话服务    │  │ - 场景管理    │
│ - 角色信息    │  │ - 状态监控    │  │ - 记忆重置    │
└───────┬───────┘  └───────────────┘  └───────┬───────┘
        │                                      │
        ▼                                      ▼
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
├── requirements.txt          # Python依赖
├── .env                      # 环境变量配置(需自行创建)
├── .gitignore               # Git忽略文件
│
├── scenes/                   # 剧本场景文件夹
│   ├── 开始-连接-结尾.txt    # 主线剧本
│   ├── scene1（xxx）.txt     # 场景1剧本
│   ├── scene2（xxx）.txt     # 场景2剧本
│   └── ...                   # 更多场景
│
├── character/                # 角色相关
│   └── trans.py             # 角色数据转换
│
└── src/                      # 源代码目录
    ├── __init__.py
    │
    ├── adapter/              # 适配器层(API服务)
    │   ├── __init__.py
    │   ├── api.py           # 玩家数据API (端口5780)
    │   ├── agent_chat.py    # AI对话API (端口5782)
    │   └── chat_launcher.py # 对话服务管理 (端口5781)
    │
    ├── agent/                # AI Agent核心
    │   ├── __init__.py
    │   ├── test_agent.py    # Agent主入口
    │   ├── chat.py          # 命令行对话
    │   ├── dice_agent.py    # 骰子Agent
    │   ├── dice_api.py      # 骰子API
    │   │
    │   ├── agentService/    # Agent服务
    │   │   ├── __init__.py
    │   │   └── service_mcp.py  # MCP服务和场景管理
    │   │
    │   └── dice/            # 骰子模块
    │       ├── __init__.py
    │       ├── dice_mcp.py  # 骰子MCP服务
    │       ├── roll.py      # 骰子投掷逻辑
    │       ├── expr.py      # 表达式解析
    │       ├── model.py     # 数据模型
    │       └── test_connection.py
    │
    ├── front/                # 前端文件
    │   ├── start.bat        # 一键启动脚本
    │   ├── game.html        # 游戏主页面
    │   ├── game.js          # 游戏主逻辑
    │   ├── chat.js          # 对话模块
    │   └── vue/             # Vue组件(备用)
    │
    └── util/                 # 工具类
        ├── __init__.py
        └── load_txt_with_keyword.py  # 剧本文件加载
```

---

## 服务端口

| 端口 | 服务 | 说明 |
|------|------|------|
| 5770 | 前端HTTP服务 | 静态文件服务，游戏页面入口 |
| 5780 | API服务 | 玩家数据、技能查询 |
| 5781 | 对话管理服务 | 管理AI对话服务的启动/停止 |
| 5782 | AI对话服务 | AI GM对话、场景管理 |

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

### 1. API服务 (端口 5780)

#### 获取玩家信息
```
GET /api/player/{player_id}
```
**响应示例:**
```json
{
  "success": true,
  "data": {
    "id": "00000001",
    "name": "调查员名称",
    "age": 28,
    "strength": 50,
    "constitution": 60,
    "hp": 12,
    "san": 65
  }
}
```

#### 获取玩家技能
```
GET /api/skills/{player_id}
```

#### 健康检查
```
GET /api/health
```

### 2. 对话管理服务 (端口 5781)

#### 启动AI对话服务
```
POST /launcher/start
```

#### 停止AI对话服务
```
POST /launcher/stop
```

#### 获取服务状态
```
GET /launcher/status
```

#### 健康检查
```
GET /launcher/health
```

### 3. AI对话服务 (端口 5782)

#### 初始化Agent
```
POST /chat/init
```

#### 发送消息
```
POST /chat/send
Content-Type: application/json

{"message": "我想调查墓地"}
```
**响应:**
```json
{
  "success": true,
  "response": "AI回复内容",
  "scene_info": {
    "scene_name": "当前场景",
    "scene_depth": 0
  }
}
```

#### 重置所有记忆
```
POST /chat/reset-all
```

#### 获取场景信息
```
GET /chat/scene
```

#### 获取日志
```
GET /chat/logs
```

#### 健康检查
```
GET /chat/health
```

---

## 前端组件

### game.html - 游戏主页面

主要区域：
- **左侧面板**: 调查员信息、属性、技能
- **中间面板**: 对话区域、消息输入
- **右侧面板**: 物品栏、可选行动

### game.js - 主逻辑

核心功能：
- `loadPlayerData()` - 加载玩家数据
- `sendMessage()` - 发送消息
- `startChat()` - 开启AI对话
- `stopChat()` - 关闭AI对话
- `resetAllMemory()` - 重置记忆

### chat.js - 对话模块

API封装：
- `ChatModule.initAgent()` - 初始化
- `ChatModule.sendMessage()` - 发送消息
- `ChatModule.startService()` - 启动服务
- `ChatModule.stopService()` - 停止服务

---

## 核心模块

### ThreadManager - 场景管理器

```python
from src.agent.agentService.service_mcp import ThreadManager

manager = ThreadManager()
manager.enter_scene("墓地")  # 进入场景
manager.exit_scene()         # 退出场景
manager.get_scene_path()     # 获取场景路径
```

### McpService - MCP工具服务

提供的工具：
- `roll_dice_tool` - 骰子投掷
- `roll_attribute_check_tool` - 属性检定
- `roll_sanity_check_tool` - 理智检定
- `new_scene` - 进入新场景
- `exit_scene` - 退出场景

---

## 剧本配置

剧本文件放置在 `scenes/` 目录下：

```
scenes/
├── 开始-连接-结尾.txt    # 主线剧本(必需)
├── scene1（xxx）.txt     # 场景文件
└── scene2（xxx）.txt
```

场景文件命名规则：文件名包含场景关键词即可被自动匹配。

---

## 开发指南

### 添加新API接口

在 `src/adapter/` 下对应文件添加：

```python
@app.get('/api/new-endpoint')
def new_endpoint():
    return {'success': True}
```

### 添加新工具

在 `src/agent/agentService/service_mcp.py` 中添加工具方法。

### 添加新场景

在 `scenes/` 目录下创建 `.txt` 文件即可。

---

## 常见问题

**Q: 端口被占用？**
A: start.bat 会自动检测并关闭占用的端口。

**Q: AI对话无响应？**
A: 检查 `.env` 中的 API Key 配置。

---

## License

MIT License
