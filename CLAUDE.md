# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Call of Cthulhu (COC) Tabletop RPG System** with an AI Game Master, built with Python FastAPI backend, vanilla JavaScript frontend, and LangChain/LangGraph for AI agent orchestration.

**Architecture**: Domain-Driven Design (DDD) with strict layering: `Adapter → Service → Domain → Infrastructure`

**LLM Models**:
- Main Agent: Alibaba Cloud Qwen (`qwen-max`) for game master conversations
- Scene Summary: Qwen3-8B for lightweight scene exit summaries

## Development Commands

```bash
# Windows - Setup and start
setup_venv.bat              # First-time setup
start.bat                   # Start frontend (5770) + backend (5780)

# Linux/Mac
./setup_venv.sh && ./start.sh

# Manual start
python -m src_test.adapter.api.main           # Backend only
cd src_test/front && python -m http.server 5770  # Frontend only

# Testing
python test_log.py                            # Test logging
python -m src_test.adapter.cli.chat           # CLI chat interface
```

### Environment Setup
Create `.env` file in project root:
```env
ALIYUN_API_KEY=your_api_key_here
ALIYUN_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Database (optional, defaults exist)
HOST=localhost
PORT=3306
USER=root
MYSQL_PW=your_password
DB_NAME=coc_game
```

## Architecture

### Directory Structure
```
src_test/
├── adapter/              # Interface layer (HTTP/CLI)
│   ├── api/             # FastAPI routes (main.py, chat_router.py, player_router.py, auth_router.py)
│   └── cli/             # Command-line interface
├── service/             # Business logic layer
│   ├── agent_service.py       # Main AI Agent with LangChain/LangGraph
│   ├── single_agent_service.py # Lightweight agent for scene summaries
│   ├── scene_service.py       # ThreadManager & McpService
│   ├── dice_service.py        # Dice rolling with database integration
│   └── player_service.py      # Player data operations
├── domain/              # Core business models (no external dependencies)
│   ├── models/          # Pydantic models (player.py, skill.py, scene.py)
│   └── dice/            # Dice expression parser & AST (roll.py, expr.py)
├── infrastructure/      # Technical services
│   ├── database/        # MySQL connection & repositories
│   ├── file/            # Scene file loader (txt_loader.py)
│   └── log/             # Loguru-based context-aware logging
└── front/               # Frontend (Vue.js 3.x via CDN)
```

### Critical Architectural Rules

**1. Strict Layering (DDD)**
- ❌ Never call across layers (e.g., Service → Database)
- ✅ Follow: Adapter → Service → Repository → Database
- Repository pattern: Services call Repository methods, never direct DB

**2. SQL Safety**
- ✅ Always use parameterized queries: `execute_query(sql, (param1,))`
- ❌ Never f-string SQL with user data
- For dynamic column names: validate with regex `^[a-zA-Z_][a-zA-Z0-9_]*$`
- Column whitelist validation in `repository.py:set_user_card()`

**3. Lazy Loading / Singletons**
- Agent services use lazy loading via `get_agent()` in chat_router.py
- Database connections use singleton pattern via `get_repository()`
- Player service via `get_player_service()`

### Key Components

**ThreadManager** (`service/scene_service.py`)
- Stack-based scene navigation with isolated memory contexts per scene
- Scene entry: validates limits, generates new thread_id, loads scene content, pushes to stack
- Scene exit: pops from stack, restores parent thread, triggers summary generation
- Scene limits defined in `scenes/scenes.txt` (format: `scene_name:max_entries`)

**Agent System** (`service/agent_service.py`)
- Uses `create_react_agent` with `InMemorySaver` checkpointer
- Dynamic prompt middleware `@dynamic_prompt` returns scene-specific prompts
- User-thread binding: `set_user_id_for_thread()` / `get_current_user_id()` pattern
- Message history tracked per thread: `thread_messages[thread_id] -> list[Message]`

**LangChain Tools** (defined in `service/agent_service.py`)
- `roll_dice_tool`: Dice rolling (e.g., "2d6+5")
- `roll_attribute_check_tool`: Attribute/skill checks using current user's character
- `roll_sanity_check_tool`: SAN checks with auto-updates to database
- `select_scene`: Enter new scenes (returns available scene list)

**Authentication** (`adapter/api/auth_router.py`)
- JWT-based auth with 24h token expiry
- Token passed via `Authorization: Bearer <token>` header
- `create_token(player_id)` / `verify_token(token)`

**SSE Streaming**
- Real-time AI responses via Server-Sent Events
- Endpoint: `/chat/send` returns `StreamingResponse`
- Stream terminates with `data: [DONE]\n\n`

## Service Ports

| Port | Service |
|------|---------|
| 5770 | Frontend (static file server) |
| 5780 | Backend (FastAPI) |
| 5780/docs | Swagger API documentation |

## Database Tables

- `players`: Character attributes (STR, DEX, SAN, HP, MP, etc.)
- `skills`: 108 skill columns per character (skill_001 to skill_108)
- `chinese_name`: ID-to-Chinese-name mapping for attributes/skills

## Logging System

Loguru-based context-aware logging in `infrastructure/log/logger.py`:
- Logs directory: `logs/{YYYYMMDD_HHMMSS}_pid{PID}/`
- Context-specific files: `api.log`, `agent.log`, `scene.log`, `dice.log`, `error.log`
- Usage: `logger = get_logger("CONTEXT")`
- Contexts: API, AGENT, SCENE, DICE

## Adding New Features

### New API Endpoint
1. Create router in `adapter/api/your_router.py`
2. Implement service in `service/your_service.py` (calls Repository)
3. Register in `adapter/api/main.py`: `app.include_router(your_router)`

### New LangChain Tool
1. Define function with `@tool` decorator in `service/agent_service.py`
2. Create Pydantic `BaseModel` for input schema if needed
3. Add to tools list in agent initialization
4. Use `get_current_user_id()` to access the current player's data

### Database Query
1. Add method to `infrastructure/database/repository.py`
2. Use parameterized queries only
3. Call from Service layer, never directly from Adapter

## Important Patterns

**User-Thread Binding**: The `thread_user_map` dict maps thread_id → user_id. Tools use `get_current_user_id()` to retrieve character data. Set via `set_user_id_for_thread()` when processing requests.

**Scene Transitions**: AI agent uses `select_scene` tool to enter new scenes. Each scene:
1. Gets a new UUID thread_id
2. Has isolated LangGraph memory
3. Loads scene-specific prompt from `scenes/*.txt`
4. Pushes to `scene_stack` for nested navigation

**Message History**: Maintained per-thread in `thread_messages` dict. Human messages appended before agent invocation, AI responses after.

**Dice Expression DSL**: Custom parser in `domain/dice/expr.py` tokenizes expressions like `2d6+5`, `3d10max` into an AST with `Roll`, `Num`, and `OpExpr` nodes. Supports post-processors: `max`, `min`, `avg`, `sum`.

**Health Checks**: Frontend polls `/chat/health` every 30s to detect backend status.

## Scene Files

Scene content is loaded from `.txt` files in the `scenes/` directory:
- `scenes.txt`: Defines scene limits (format: `scene_name:max_entries`)
- `开始-连接-结尾.txt`: Main storyline content
- `scene_xxx.txt`: Individual scene content

Each scene's system prompt combines base `SCENE_PROMPT` (GM guidelines) + scene-specific content.
