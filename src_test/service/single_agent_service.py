"""
Single Agent 服务
用于场景总结等简单任务
"""

import os
from dotenv import load_dotenv
from src_test.infrastructure.log import get_logger

logger = get_logger("AGENT")
from langchain_openai import ChatOpenAI

# 加载环境变量
load_dotenv(override=True)

# 初始化模型
MODELSCOPE_API_KEY = os.getenv("MODELSCOPE_API_KEY")
MODELSCOPE_URL = os.getenv("MODELSCOPE_URL")

logger.info("初始化Qwen3-8B模型（用于场景总结）...")
model = ChatOpenAI(
    model="Qwen/Qwen3-8B",
    api_key=MODELSCOPE_API_KEY,
    base_url=MODELSCOPE_URL,
    temperature=0.7,
    extra_body={"enable_thinking": False}
)
logger.info("场景总结模型初始化完成")
