import os
import json
import sys
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain.messages import HumanMessage, AIMessage, SystemMessage
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langgraph.checkpoint.memory import InMemorySaver
from typing import Optional, Dict, Any

# 导入骰子服务
from dice.dice_mcp import DiceService

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 从 service_mcp 导入场景管理相关类
from src.agent.agentService.service_mcp import ThreadManager, McpService, MAIN_PROMPT

# 加载环境变量
load_dotenv(override=True)

# 创建全局线程管理器和MCP服务（使用默认的scenes目录）
thread_manager = ThreadManager()
mcp_service = McpService(thread_manager=thread_manager)

# 初始化骰子服务
dice_service = DiceService()

# 定义工具参数模型
class RollDiceInput(BaseModel):
    expression: str = Field(description="骰子表达式字符串，例如 '2d10+5' 或 '3d6'")
    is_hidden: bool = Field(default=False, description="是否为暗骰。如果是，结果应只对调用者可见")

class AttributeCheckInput(BaseModel):
    user_id: str = Field(description="执行检定的用户ID，用于查找角色卡")
    attribute_name: str = Field(description="要检定的属性或技能名称，例如 '力量', '侦查'，'图书馆使用'，'闪避'")
    target_value: Optional[int] = Field(default=None, description="检定的目标值。如果未提供，将自动从用户的角色卡中查找")

class SanityCheckInput(BaseModel):
    user_id: str = Field(description="执行检定的用户ID")
    success_penalty: str = Field(description="检定成功时理智惩罚的骰子表达式, 例如 '1'")
    failure_penalty: str = Field(description="检定失败时理智惩罚的骰子表达式, 例如 '1d6'")

# 定义工具
@tool(args_schema=RollDiceInput)
def roll_dice_tool(expression: str, is_hidden: bool = False) -> str:
    """
    执行一个标准的骰子投掷表达式。

    例如，当用户说"丢个2d10+5"或".r 2d10+5"时，LLM应调用此函数。

    :param expression: 骰子表达式字符串，例如 "2d10+5" 或 "3d6"。
    :param is_hidden: 是否为暗骰。如果是，结果应只对调用者可见，默认不需要传该参数。
    :return: 一个包含投掷结果和计算过程的字典。
                例如: {'result': 15, 'process': '2d10(5, 10) + 5 = 15'}
    """
    result = dice_service.roll_dice(expression, is_hidden)
    return json.dumps(result, ensure_ascii=False)

@tool(args_schema=AttributeCheckInput)
def roll_attribute_check_tool(user_id: str, attribute_name: str, target_value: Optional[int] = None) -> str:
    """
    对用户的某个属性或技能进行检定（1d100）。

    例如，当用户说"进行一次力量检定"，"进行一次说服检定"，".ra 力量"，".ra 说服"等类似请求时，LLM应调用此函数。

    :param user_id: 执行检定的用户ID，用于查找角色卡。
    :param attribute_name: 要检定的属性或技能名称，例如 "力量", "侦查"，"图书馆使用"，"闪避"。
    :param target_value: (可选) 检定的目标值。默认不提供，将自动从用户的角色卡中查找。
    :return: 包含检定结果、目标值、成功等级的字典。
    """
    result = dice_service.roll_attribute_check(user_id, attribute_name, target_value)
    return json.dumps(result, ensure_ascii=False)

@tool(args_schema=SanityCheckInput)
def roll_sanity_check_tool(user_id: str, success_penalty: str, failure_penalty: str) -> str:
    """
    为用户执行一次理智检定（Sanity Check）。

    例如，当用户说"sc 1/1d6"或"对理智值进行检定，惩罚为1/1d6"时，LLM应解析出参数并调用此函数。

    :param user_id: 执行检定的用户ID。
    :param success_penalty: 检定成功时理智惩罚的骰子表达式, 例如 "1"。
    :param failure_penalty: 检定失败时理智惩罚的骰子表达式, 例如 "1d6"。
    :return: 包含检定结果、SAN值变化的详细字典。
    """
    result = dice_service.roll_sanity_check(user_id, success_penalty, failure_penalty)
    return json.dumps(result, ensure_ascii=False)


# 定义工具（包装 McpService 的方法）
@tool()
def new_scene(scene: str) -> str:
    """
    进入新的场景。

    当模型判断需要进入新场景时调用此函数。
    这将切换到一个新的记忆线程，使用场景特定的提示词（从txt文件加载）。
    支持嵌套场景：可以在一个场景中进入另一个场景。

    :param scene: 场景名称/关键词。
    :return: 场景进入确认信息
    """
    return mcp_service.new_scene(scene)


@tool()
def exit_scene() -> str:
    """
    退出当前场景，返回上一个场景或主线程。

    当场景探索完成或玩家要求离开时调用此函数。
    如果当前在嵌套场景中，会返回到上一层场景；
    如果只有一层场景，会返回到主线程。

    :return: 退出确认信息
    """
    return mcp_service.exit_scene()


# 动态提示词中间件
@dynamic_prompt
def dynamic_system_prompt(request: ModelRequest) -> str:
    """根据当前状态动态返回系统提示词"""
    return thread_manager.get_current_prompt()


# 初始化模型
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_URL = os.getenv("DEEPSEEK_URL")

model = ChatDeepSeek(
    model="deepseek-chat",
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_URL,
    temperature=1.2
)

# 创建checkpointer用于记忆持久化
checkpointer = InMemorySaver()

tools = [
    roll_dice_tool,
    roll_attribute_check_tool,
    roll_sanity_check_tool,
    new_scene,
    exit_scene
]

# 创建Agent，使用动态提示词中间件和checkpointer
agent = create_agent(
    model=model,
    tools=tools,
    middleware=[dynamic_system_prompt],
    checkpointer=checkpointer
)
