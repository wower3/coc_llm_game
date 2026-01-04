# COC 跑团游戏系统 (AI参考文档)

> 基于 LangChain + DeepSeek + FastAPI 的克苏鲁神话跑团游戏系统

## 项目结构

```
coc_structure/
├── src_test/              # 重构后的源代码(DDD架构)
│   ├── adapter/           # 适配器层 - API/CLI入口
│   ├── service/           # 服务层 - 业务逻辑
│   ├── domain/            # 领域层 - 核心模型
│   └── infrastructure/    # 基础设施层 - DB/文件/日志
├── scenes/                # 剧本文件
└── logs/                  # 日志目录(自动生成)
```

---

## 后端文件 (src_test/adapter/)

### api/main.py
- **功能**: FastAPI主入口，整合所有子路由
- **端口**: 5780
- **职责**: 注册player_router、chat_router、auth_router，配置CORS

### api/chat_router.py
- **功能**: AI对话服务路由
- **前缀**: `/chat`
- **接口**:
  - `POST /chat/send` - 发送消息(SSE流式输出)
  - `POST /chat/init` - 初始化Agent
  - `POST /chat/reset-all` - 重置所有场景记忆
  - `GET /chat/scene` - 获取当前场景信息
  - `GET /chat/logs` - 获取系统日志
  - `GET /chat/log-file` - 获取实时日志文件内容(all.log)
  - `POST /chat/scene/new` - 进入新场景
  - `POST /chat/scene/exit` - 退出当前场景
- **核心变量**:
  - `thread_messages` - 字典，按线程ID隔离消息历史
- **记忆隔离**: 每个场景有独立的thread_id和消息列表
- **日志**: 使用loguru记录所有API请求和响应

### api/player_router.py
- **功能**: 玩家数据API路由
- **前缀**: `/api`
- **接口**:
  - `GET /api/player/{id}` - 获取玩家属性(力量、体质、理智等)
  - `GET /api/skills/{id}` - 获取玩家技能列表
  - `GET /api/health` - 健康检查

### cli/chat.py
- **功能**: 命令行对话入口
- **用途**: 本地测试Agent对话
- **特性**: 支持场景切换、记忆隔离
- **日志**: 记录所有用户输入和AI回复

---

## 服务文件 (src_test/service/)

### agent_service.py
- **功能**: LangChain Agent主入口
- **导出**: `agent`, `thread_manager`, `checkpointer`, `available_scenes`
- **模型**: DeepSeek (temperature=1.2)
- **MCP工具**:
  - `roll_dice_tool` - 骰子投掷 (如"2d6+5")
  - `roll_attribute_check_tool` - 属性/技能检定
  - `roll_sanity_check_tool` - 理智检定 (如"sc 1/1d6")
  - `select_scene` - 提供场景选择按钮
  - `new_scene` - 进入新场景
  - `exit_scene` - 退出当前场景
- **中间件**: `dynamic_system_prompt` 动态切换提示词
- **日志**: 记录所有工具调用和Agent交互

### scene_service.py
- **核心类**:
  - `ThreadManager` - 场景管理器
    - `scene_stack` - 场景栈(支持嵌套)
    - `scene_limits` - 场景进入次数限制
    - `entered_count` - 已进入次数统计
    - `enter_scene(name)` - 进入场景，创建新线程
    - `exit_scene()` - 退出场景，返回上层
    - `get_current_prompt()` - 获取当前场景提示词
    - `get_available_scenes()` - 获取可进入场景列表
  - `McpService` - MCP工具服务封装
- **提示词**: `BASE_PROMPT`, `SCENE_PROMPT`, `SCENE_GUIDANCE`
- **日志**: 记录所有场景切换操作

### dice_service.py
- **功能**: 骰子服务
- **类**: `DiceService`
  - `roll_dice(expr, is_hidden)` - 投掷骰子
  - `roll_attribute_check(user_id, attr)` - 属性检定
  - `roll_sanity_check(user_id, success, fail)` - 理智检定
  - `set_character_attributes(user_id, attrs)` - 设置角色属性
  - `get_character_sheet(user_id)` - 获取角色卡
  - `generate_coc_character_sheet(count)` - 生成角色卡
- **日志**: 记录所有骰子投掷和检定结果

---

## 领域文件 (src_test/domain/)

### models/player.py
- 玩家数据模型 (Player)

### models/skill.py
- 技能数据模型 (Skill)

### models/scene.py
- 场景信息模型 (SceneInfo)

### dice/roll.py
- 骰子投掷核心逻辑

### dice/expr.py
- 骰子表达式解析

---

## 基础设施文件 (src_test/infrastructure/)

### database/connection.py
- 数据库连接管理

### database/repository.py
- 数据仓库 (DataContainer)
- 方法: `get_skill_card()`, `get_player()`, `get_user_card()`, `set_user_card()`

### file/txt_loader.py
- 剧本文件加载器 (TxtKeywordSearch)

### log/logger.py
- **日志配置模块**
- 使用loguru实现分类日志记录
- **日志结构**: 每次运行创建独立文件夹 `{YYYYMMDD_HHMMSS}_pid{PID}/`
- **日志文件**:
  - `all.log` - 所有日志(DEBUG)
  - `api.log` - API日志(INFO)
  - `agent.log` - Agent日志(DEBUG)
  - `scene.log` - 场景日志(INFO)
  - `dice.log` - 骰子日志(INFO)
  - `error.log` - 错误日志(ERROR)
- **归档**: 使用 `logs/归档旧日志.bat` 将旧日志压缩到 `history/{YYYYMMDD}/`
- **特性**:
  - 独立文件夹(启动时间+进程ID)
  - 自动轮转(每天午夜)
  - 自动压缩(zip)
  - 自动清理(30天)
  - 上下文过滤(API/AGENT/SCENE/DICE/CLI)

---

## 日志系统

项目使用 **loguru** 实现全面的调试日志。

### 日志结构

每次运行创建独立文件夹: `logs/{YYYYMMDD_HHMMSS}_pid{PID}/`

| 上下文 | 文件 | 内容 |
|--------|------|------|
| `API` | api.log | API请求/响应 |
| `AGENT` | agent.log | Agent交互 |
| `SCENE` | scene.log | 场景切换 |
| `DICE` | dice.log | 骰子投掷 |
| - | all.log | 全部日志 |
| - | error.log | 错误日志 |

**文件夹命名**: `{日期时分秒}_pid{进程ID}`
- 示例: `20260104_105942_pid40972/`
- 每次运行生成独立文件夹，不会覆盖

### 日志归档

- 脚本: `logs/归档旧日志.bat`
- 功能: 将昨天及之前的日志压缩到 `history/{YYYYMMDD}/`

### 使用方式

```python
from src_test.infrastructure.log import get_logger

# 获取带上下文的logger
logger = get_logger("API")  # 或 "AGENT", "SCENE", "DICE", "CLI"

# 记录日志
logger.info("操作信息")
logger.error("错误信息", exc_info=True)
```

---

## 关键设计

| 设计 | 说明 |
|------|------|
| DDD架构 | adapter/service/domain/infrastructure分层 |
| 记忆隔离 | `thread_messages`字典按thread_id隔离各场景消息 |
| 场景栈 | `ThreadManager.scene_stack`支持嵌套场景 |
| 流式输出 | SSE格式(`data: xxx\n\n`)返回AI响应 |
| 动态提示词 | 根据当前场景自动切换system prompt |
| 日志记录 | 所有调用、传输、错误都记录到logs/目录 |
| 健康检测 | 每30秒自动检测后端服务状态 |
| Git忽略 | logs/、*.log、.env、.claude/ 已配置忽略 |

---

## 测试

```bash
# 测试日志功能
python test_log.py

# 测试CLI对话
python -m src_test.adapter.cli.chat
```
