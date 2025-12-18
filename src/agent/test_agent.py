import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain.messages import HumanMessage, AIMessage, SystemMessage
from typing import Optional, Dict, Any
import json

# 加载环境变量
load_dotenv(override=True)

# 创建提示词模板
prompt = """
你是一个克苏鲁神话角色扮演游戏(CoC)的智能游戏主持人(GM)，能够帮助玩家进行各种骰子投掷和角色管理。

在对话过程中，请遵循以下规则：
- 理解玩家的意图并选择合适的工具
- 准确提取必要的参数
- 清晰地解释骰子结果和检定含义
- 保持克苏鲁神话的氛围和风格

请记住，你是玩家在神秘和危险的克苏鲁世界中的骰子智能体，你的职责是确保骰子结果符合规则，不需要进行太多的延申。
"""

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
agent = create_agent(model=model, system_prompt=prompt)
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

        print(f"/n*******************/n{messages}/n*******************/n")

        # 保持消息长度（只保留最近50轮）
        messages = messages[-50:]

if __name__ == "__main__":
    main()