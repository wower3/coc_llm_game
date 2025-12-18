import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain.messages import HumanMessage, AIMessage, SystemMessage
from typing import Optional, Dict, Any
import json

# 导入骰子服务
from dice.dice_mcp import DiceService

# 加载环境变量
load_dotenv(override=True)

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

    例如，当用户说“丢个2d10+5”或“.r 2d10+5”时，LLM应调用此函数。

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

    例如，当用户说“进行一次力量检定”，“进行一次说服检定”，“.ra 力量”，“.ra 说服”等类似请求时，LLM应调用此函数。

    :param user_id: 执行检定的用户ID，用于查找角色卡。
    :param attribute_name: 要检定的属性或技能名称，例如 "力量", "侦查"，“图书馆使用”，“闪避”。
    :param target_value: (可选) 检定的目标值。默认不提供，将自动从用户的角色卡中查找。
    :return: 包含检定结果、目标值、成功等级的字典。
    """
    result = dice_service.roll_attribute_check(user_id, attribute_name, target_value)
    return json.dumps(result, ensure_ascii=False)

@tool(args_schema=SanityCheckInput)
def roll_sanity_check_tool(user_id: str, success_penalty: str, failure_penalty: str) -> str:
    """
    为用户执行一次理智检定（Sanity Check）。

    例如，当用户说“sc 1/1d6”或“对理智值进行检定，惩罚为1/1d6”时，LLM应解析出参数并调用此函数。

    :param user_id: 执行检定的用户ID。
    :param success_penalty: 检定成功时理智惩罚的骰子表达式, 例如 "1"。
    :param failure_penalty: 检定失败时理智惩罚的骰子表达式, 例如 "1d6"。
    :return: 包含检定结果、SAN值变化的详细字典。
    """
    result = dice_service.roll_sanity_check(user_id, success_penalty, failure_penalty)
    return json.dumps(result, ensure_ascii=False)

# 创建提示词模板
prompt = """
你是一个克苏鲁神话角色扮演游戏(CoC)的智能游戏主持人(GM)，能够帮助玩家进行各种骰子投掷和角色管理。

如有需要，使用以下mcp工具来协助玩家：

1. **骰子投掷 请调用"roll_dice_tool"工具:**:
   - 当玩家需要投掷骰子时使用，例如"投掷2d10+5"或"r 1d100"
   - 支持标准的骰子表达式，如"1d6"、"2d10+5"、"3d6*5"等
   - 可以进行暗骰(is_hidden=True)，结果只对指定玩家显示

2. **属性或技能检定 请调用"roll_attribute_check_tool"工具:
   - 当玩家需要进行属性或技能检定时（例如"进行力量检定"或".ra 侦查"）使用，使用"roll_attribute_check_tool"工具
   - 需要提供玩家ID和属性或技能名称
   - 目标值target_value未提供时不需要该传参。

3. **理智检定 请调用“roll_sanity_check_tool”工具**:
   - 当玩家角色需要进行理智检定时使用，例如"sc 1/1d6"（表示检定成功时理智惩罚的骰子表达式为"1",失败时理智惩罚的骰子表达式为"1d6"）
   - 需要提供玩家ID以及成功和失败时的理智损失表达式

在对话过程中，请遵循以下规则：
- 理解玩家的意图并选择合适的工具
- 准确提取必要的参数
- 清晰地解释骰子结果和检定含义
- 保持克苏鲁神话的氛围和风格

请记住，你是玩家在神秘和危险的克苏鲁世界中的骰子智能体，你的职责是确保骰子结果符合规则，不需要进行太多的延申。
"""

# 定义可用工具
tools = [
    roll_dice_tool,
    roll_attribute_check_tool,
    roll_sanity_check_tool
]

# 初始化模型
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_URL = os.getenv("DEEPSEEK_URL")

model = ChatDeepSeek(
    model="deepseek-chat",
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_URL,
    temperature=1.2
)

# 创建Agent
agent = create_agent(model=model, tools=tools, system_prompt=prompt)
system_message = SystemMessage(
    content=prompt
)

# 主对话循环
def main():
    print("🎲 欢迎来到克苏鲁神话角色扮演游戏!")
    print("🔹 输入 'exit' 或 'quit' 退出游戏\n")

    # 初始化对话历史
    messages = [system_message]

    while True:
        user_input = input("👤 玩家: ")
        if user_input.lower() in {"exit", "quit"}:
            print("游戏副本结束，期待下次冒险再见！")
            break

        # 使用agent处理用户输入
        messages.append(HumanMessage(content=user_input))

        # 显示AI回复
        print("🤖 游戏主持人:", end="", flush=True)
        response = agent.invoke({"messages":messages})
        result = response["messages"][-1].content

        # ✅ LangChain 1.0 标准写法
        print(result)
        print("\n" + "-" * 40)  # 分隔线

        # 更新对话历史
        messages.append(AIMessage(content=result))

        # 保持消息长度（只保留最近50轮）
        messages = messages[-50:]

if __name__ == "__main__":
    main()