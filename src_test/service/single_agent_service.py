"""
Agent 服务
从原 agent/test_agent.py 提取
"""

import os
import json
from dotenv import load_dotenv
from src_test.infrastructure.log import get_logger

logger = get_logger("AGENT")
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from pydantic import BaseModel, Field
from langchain.agents.middleware import dynamic_prompt, ModelRequest

# 加载环境变量
load_dotenv(override=True)


# 动态提示词中间件
@dynamic_prompt
def dynamic_system_prompt(request: ModelRequest) -> str:
    """根据当前状态动态返回系统提示词"""
    return ""


# 初始化模型
MODELSCOPE_API_KEY = os.getenv("MODELSCOPE_API_KEY")
MODELSCOPE_URL = os.getenv("MODELSCOPE_URL")

logger.info("初始化DeepSeek模型...")
model = ChatOpenAI(
    model="Qwen/Qwen3-8B",
    api_key=MODELSCOPE_API_KEY,
    base_url=MODELSCOPE_URL,
    temperature=1.0,
    extra_body={"enable_thinking": False}
)

# 创建Agent，使用动态提示词中间件和checkpointer
logger.info("创建Agent，配置工具和中间件...")
agent = create_agent(
    model=model
)
logger.info("Agent初始化完成")
