# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Call of Cthulhu (COC) Tabletop RPG System** with an AI Game Master, built with Python FastAPI backend, vanilla JavaScript frontend, and LangChain/LangGraph for AI agent orchestration using DeepSeek LLM.

**Architecture**: Domain-Driven Design (DDD) with strict layering: `Adapter → Service → Domain → Infrastructure`

## Development Commands

### Quick Start
```bash
# Windows - Setup virtual environment and install dependencies
setup_venv.bat

# Windows - Start both frontend (port 5770) and backend (port 5780)
start.bat

# Linux/Mac - Setup
chmod +x setup_venv.sh && ./setup_venv.sh

# Linux/Mac - Start
./start.sh
```

### Manual Start
```bash
# Activate virtual environment
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/Mac

# Start backend (port 5780)
python -m src_test.adapter.api.main

# Start frontend (port 5770) - in separate terminal
cd src_test/front
python -m http.server 5770
```

### Testing
```bash
# Test logging system
python test_log.py

# Test CLI chat interface
python -m src_test.adapter.cli.chat
```

### Environment Setup
Create `.env` file in project root:
```env
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_URL=https://api.deepseek.com

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
│   ├── api/             # FastAPI routes (main.py, chat_router.py, player_router.py)
│   └── cli/             # Command-line interface
├── service/             # Business logic layer
│   ├── agent_service.py       # AI Agent with LangChain/LangGraph
│   ├── scene_service.py       # Scene/thread management
│   ├── dice_service.py        # Dice rolling
│   └── player_service.py      # Player data operations
├── domain/              # Core business models (no external dependencies)
│   ├── models/          # Pydantic models (player.py, skill.py, scene.py)
│   └── dice/            # Dice logic (roll.py, expr.py)
├── infrastructure/      # Technical services
│   ├── database/        # MySQL connection & repositories
│   ├── file/            # File operations (scene loader)
│   └── log/             # Loguru-based logging
└── front/               # Frontend (Vue.js 3.x via CDN, vanilla JS)
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

**3. Dependency Injection**
- Agent services use lazy loading via `get_agent()` in chat_router.py
- Database connections use singleton pattern via `get_repository()`

### Key Components

**ThreadManager** (`service/scene_service.py`)
- Manages nested scenes with isolated memory contexts
- Scene stack for navigation: `enter_scene()`, `exit_scene()`
- Each scene has independent LangGraph thread/memory

**MCP Tools** (`service/agent_service.py`)
- `roll_dice_tool`: Dice rolling (e.g., "2d6+5")
- `roll_attribute_check_tool`: Attribute/skill checks using current user's character
- `roll_sanity_check_tool`: SAN checks with auto-updates
- `select_scene_tool`: Enter new scenes
- `exit_scene_tool`: Exit current scene

**SSE Streaming**
- Real-time AI responses via Server-Sent Events
- Endpoint: `/chat/send` returns `StreamingResponse`

## Service Ports

| Port | Service |
|------|---------|
| 5770 | Frontend (static file server) |
| 5780 | Backend (FastAPI) |
| 5780/docs | Swagger API documentation |

## Database Tables

- `players`: Character stats (strength, dexterity, HP, MP, SAN, etc.)
- `skills`: 80+ skill values per character
- `chinese_name`: Mapping of Chinese attribute/skill names to IDs

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

### New MCP Tool
1. Define function with `@tool` decorator in `service/agent_service.py`
2. Create Pydantic `BaseModel` for input schema
3. Add to tools list in agent initialization

### Database Query
1. Add method to `infrastructure/database/repository.py`
2. Use parameterized queries only
3. Call from Service layer, never directly from Adapter

## Important Patterns

**Agent-User Binding**: Tools use `get_current_user_id()` to retrieve character data for logged-in users. User ID is stored per-thread via `set_user_id_for_thread()`.

**Scene Transitions**: AI agent uses `select_scene_tool` to enter new scenes, which pushes to scene stack. Each scene has isolated LangGraph memory thread.

**Health Checks**: Frontend polls `/chat/health` every 30s to detect backend status.
