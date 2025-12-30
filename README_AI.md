# COC 跑团游戏系统 (AI参考文档)

> 基于 LangChain + DeepSeek + FastAPI 的克苏鲁神话跑团游戏系统

## 项目结构

```
coc_structure/
├── src/adapter/          # 后端API (端口5780)
├── src/agent/            # AI Agent核心
├── src/front/            # 前端 (端口5770)
├── src/util/             # 工具类
└── scenes/               # 剧本文件
```

---

## 后端文件 (src/adapter/)

### backend_api.py
- **功能**: FastAPI主入口，整合所有子路由
- **端口**: 5780
- **职责**: 注册player_router和chat_router，配置CORS

### player_router.py
- **功能**: 玩家数据API路由
- **前缀**: `/api`
- **接口**:
  - `GET /api/player/{id}` - 获取玩家属性(力量、体质、理智等)
  - `GET /api/skills/{id}` - 获取玩家技能列表
  - `GET /api/health` - 健康检查

### chat_router.py
- **功能**: AI对话服务路由
- **前缀**: `/chat`
- **接口**:
  - `POST /chat/send` - 发送消息(SSE流式输出)
  - `POST /chat/init` - 初始化Agent
  - `POST /chat/reset-all` - 重置所有场景记忆
  - `GET /chat/scene` - 获取当前场景信息
  - `GET /chat/logs` - 获取系统日志
- **核心变量**:
  - `thread_messages` - 字典，按线程ID隔离消息历史
- **记忆隔离**: 每个场景有独立的thread_id和消息列表

---

## Agent文件 (src/agent/)

### test_agent.py
- **功能**: LangChain Agent主入口
- **导出**: `agent`, `thread_manager`, `checkpointer`
- **模型**: DeepSeek (temperature=1.2)
- **MCP工具**:
  - `roll_dice_tool` - 骰子投掷 (如"2d6+5")
  - `roll_attribute_check_tool` - 属性/技能检定
  - `roll_sanity_check_tool` - 理智检定 (如"sc 1/1d6")
  - `new_scene` - 进入新场景
  - `exit_scene` - 退出当前场景
- **中间件**: `dynamic_system_prompt` 动态切换提示词

### chat.py
- **功能**: 命令行对话入口
- **用途**: 本地测试Agent对话
- **特性**: 支持场景切换、记忆隔离

### agentService/service_mcp.py
- **功能**: 场景管理和MCP服务
- **核心类**:
  - `ThreadManager` - 场景管理器
    - `scene_stack` - 场景栈(支持嵌套)
    - `enter_scene(name)` - 进入场景，创建新线程
    - `exit_scene()` - 退出场景，返回上层
    - `get_current_prompt()` - 获取当前场景提示词
  - `McpService` - MCP工具服务封装
- **提示词**: `BASE_PROMPT`, `SCENE_PROMPT`, `EXIT_SCENE_TOOL`

### dice/dice_mcp.py
- **功能**: 骰子服务
- **类**: `DiceService`
  - `roll_dice(expr)` - 投掷骰子
  - `roll_attribute_check(user_id, attr)` - 属性检定
  - `roll_sanity_check(user_id, success, fail)` - 理智检定

### dice/model.py
- **功能**: 数据模型和数据库连接
- **类**: `DataContainer` - MySQL数据库操作
- **方法**: `get_skill_card()`, `get_player()`

---

## 前端文件 (src/front/)

### game.html
- **功能**: 游戏主页面
- **布局**:
  - 左侧: 调查员属性、技能列表
  - 中间: 对话区域、消息输入
  - 右侧: 物品栏、可选行动
- **顶部菜单**: 重置记忆、存档、读档

### game.js
- **功能**: 游戏主逻辑
- **核心方法**:
  - `checkChatStatus()` - 检查服务状态，自动初始化Agent
  - `sendMessage()` - 发送消息到AI
  - `sendToAI()` - 流式接收AI回复
  - `resetAllMemory()` - 重置所有记忆
  - `loadPlayerData()` - 加载玩家数据

### chat.js
- **功能**: 对话模块，封装后端API调用
- **对象**: `ChatModule`
- **核心方法**:
  - `checkStatus()` - 检查后端服务状态
  - `initAgent()` - 初始化Agent
  - `sendMessage(msg, onToken, onComplete, onError)` - 流式发送消息
  - `resetAllMemory()` - 重置所有记忆
- **配置**: `CHAT_API_URL = 'http://localhost:5780/chat'`

### start.bat
- **功能**: 一键启动脚本
- **启动服务**:
  1. 后端服务 (端口5780)
  2. 前端HTTP服务 (端口5770)
- **自动处理**: 端口占用检测和清理

---

## 关键设计

| 设计 | 说明 |
|------|------|
| 记忆隔离 | `thread_messages`字典按thread_id隔离各场景消息 |
| 场景栈 | `ThreadManager.scene_stack`支持嵌套场景 |
| 流式输出 | SSE格式(`data: xxx\n\n`)返回AI响应 |
| 动态提示词 | 根据当前场景自动切换system prompt |
