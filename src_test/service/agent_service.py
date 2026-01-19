"""
Agent 服务
从原 agent/test_agent.py 提取
"""

import os
import json
from dotenv import load_dotenv
from src_test.infrastructure.log import get_logger

logger = get_logger("AGENT")
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langgraph.checkpoint.memory import InMemorySaver

from src_test.service.scene_service import ThreadManager, McpService
from src_test.service.dice_service import DiceService

# 加载环境变量
load_dotenv(override=True)

# 初始化服务
thread_manager = ThreadManager()
mcp_service = McpService(thread_manager)
dice_service = DiceService()
checkpointer = InMemorySaver()

# AI返回的场景选择列表（用于存储AI通过select_scene工具返回的场景）
available_scenes: list[str] = []

# thread_id -> user_id 映射（用于存储每个线程对应的用户ID）
thread_user_map: dict[str, str] = {}


def set_user_id_for_thread(thread_id: str, user_id: str):
    """设置指定线程的用户ID"""
    thread_user_map[thread_id] = user_id
    logger.debug(f"[AGENT] 设置线程用户映射: {thread_id[:8]} -> {user_id}")


def get_current_user_id() -> str:
    """获取当前线程对应的用户ID"""
    current_thread_id = thread_manager.current_thread_id
    user_id = thread_user_map.get(current_thread_id)
    logger.debug(f"[AGENT] 获取当前用户ID: thread_id={current_thread_id[:8]}, user_id={user_id}")
    return user_id


# 定义工具参数模型
class RollDiceInput(BaseModel):
    expression: str = Field(description="骰子表达式字符串，例如 '2d10+5' 或 '3d6'")
    is_hidden: bool = Field(default=False, description="是否为暗骰。如果是，结果应只对调用者可见")


class AttributeCheckInput(BaseModel):
    attribute_name: str = Field(description="要检定的属性或技能名称，例如 '力量', '侦查'，'图书馆使用'，'闪避'")


class SanityCheckInput(BaseModel):
    success_penalty: str = Field(description="检定成功时理智惩罚的骰子表达式, 例如 '1'")
    failure_penalty: str = Field(description="检定失败时理智惩罚的骰子表达式, 例如 '1d6'")


# 定义工具函数
@tool(args_schema=RollDiceInput)
def roll_dice_tool(expression: str, is_hidden: bool = False) -> str:
    """
    执行一个标准的骰子投掷表达式。

    例如，当用户说"丢个2d10+5"或".r 2d10+5"时，LLM应调用此函数。

    :param expression: 骰子表达式字符串，例如 "2d10+5" 或 "3d6"。
    :param is_hidden: 是否为暗骰。如果是，结果应只对调用者可见，默认不需要传该参数。
    :return: 一个包含投掷结果和计算过程的字典。
    """
    logger.info(f"[骰子投掷] 表达式: {expression}, 暗骰: {is_hidden}")
    result = dice_service.roll_dice(expression, is_hidden)
    logger.info(f"[骰子投掷] 结果: {result}")
    return json.dumps(result, ensure_ascii=False)


@tool(args_schema=AttributeCheckInput)
def roll_attribute_check_tool(attribute_name: str) -> str:
    """
    对当前登录用户的某个属性或技能进行检定（1d100）。

    例如，当用户说"进行一次力量检定"，"进行一次说服检定"，".ra 力量"，".ra 说服"等类似请求时，LLM应调用此函数。
    系统会自动使用当前登录用户的ID来查找角色卡。

    :param attribute_name: 要检定的属性或技能名称，例如 "力量", "侦查"，"图书馆使用"，"闪避"。
    :return: 包含检定结果、目标值、成功等级的字典。
    """
    user_id = get_current_user_id()
    if not user_id:
        logger.warning("[属性检定] 未找到用户ID，请确保已登录")
        return json.dumps({"error": "未找到用户信息，请先登录"}, ensure_ascii=False)

    logger.info(f"[属性检定] 用户ID: {user_id}, 属性: {attribute_name}")
    result = dice_service.roll_attribute_check(user_id, attribute_name)
    logger.info(f"[属性检定] 结果: {result}")
    return json.dumps(result, ensure_ascii=False)


@tool(args_schema=SanityCheckInput)
def roll_sanity_check_tool(success_penalty: str, failure_penalty: str) -> str:
    """
    为当前登录用户执行一次理智检定（Sanity Check）。

    例如，当用户说"sc 1/1d6"或"对理智值进行检定，惩罚为1/1d6"时，LLM应解析出参数并调用此函数。
    系统会自动使用当前登录用户的ID来查找角色卡。

    :param success_penalty: 检定成功时理智惩罚的骰子表达式, 例如 "1"。
    :param failure_penalty: 检定失败时理智惩罚的骰子表达式, 例如 "1d6"。
    :return: 包含检定结果、SAN值变化的详细字典。
    """
    user_id = get_current_user_id()
    if not user_id:
        logger.warning("[理智检定] 未找到用户ID，请确保已登录")
        return json.dumps({"error": "未找到用户信息，请先登录"}, ensure_ascii=False)

    logger.info(f"[理智检定] 用户ID: {user_id}, 成功惩罚: {success_penalty}, 失败惩罚: {failure_penalty}")
    result = dice_service.roll_sanity_check(user_id, success_penalty, failure_penalty)
    logger.info(f"[理智检定] 结果: {result}")
    return json.dumps(result, ensure_ascii=False)


@tool
def select_scene(scenes: str) -> str:
    """
    提供可以进入的场景按钮。

    当明确提到调用"select_scene"时调用此函数，否则不要调用这个工具。
    将场景名称以空格分隔传入。

    :param scenes: 场景名称/关键词，用空格分隔，例如 "场景A 场景B 场景C"
    """
    global available_scenes
    # 解析场景列表
    available_scenes = mcp_service.select_scene(scenes)
    return "调用成功，输出：场景已经更新完成。"

@tool
def get_item(item: str) -> str:
    """
    当玩家获得某样物品时调用此函数。

    当判断出用户获得（买到，捡到等关键词）某个道具时调用此函数。
    将物品名称作为参数传入。

    :param scenes: 场景名称/关键词，用空格分隔，例如 "场景A 场景B 场景C"
    :return: 场景列表已更新的确认信息
    """
    return "可选场景已更新"

# 工具列表
tools = [roll_dice_tool, roll_attribute_check_tool, roll_sanity_check_tool, select_scene]


# 动态提示词中间件
@dynamic_prompt
def dynamic_system_prompt(request: ModelRequest) -> str:
    """根据当前状态动态返回系统提示词"""
    return thread_manager.get_current_prompt()


# 初始化模型
ALIYUN_API_KEY = os.getenv("ALIYUN_API_KEY")
ALIYUN_URL = os.getenv("ALIYUN_URL")

logger.info("初始化DeepSeek模型...")
model = ChatOpenAI(
    model="qwen-max",
    api_key=ALIYUN_API_KEY,
    base_url=ALIYUN_URL,
    temperature=1.5,
    presence_penalty=0.3
)

# 创建Agent，使用动态提示词中间件和checkpointer
logger.info("创建Agent，配置工具和中间件...")
agent = create_agent(
    model=model,
    tools=tools,
    middleware=[dynamic_system_prompt],
    checkpointer=checkpointer
)
logger.info("Agent初始化完成")
